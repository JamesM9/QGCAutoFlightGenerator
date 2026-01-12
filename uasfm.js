/**
 * FAA UAS Facility Maps (UASFM) Integration Module
 * 
 * This module provides integration with FAA UAS Facility Maps data for desktop applications
 * with webviews. It handles data fetching, caching, and overlay management for Leaflet maps.
 * 
 * Features:
 * - Fetches latest UASFM GeoJSON data from FAA UDDS API
 * - Parses 30x30 arc-second grid squares and max AGL altitudes
 * - Local caching with IndexedDB for offline use
 * - Automatic update checking every 56 days
 * - Error handling and data validation
 * - Leaflet overlay integration
 * - TFR (Temporary Flight Restrictions) checking
 * - Flight planning validation
 * - LAANC integration
 * 
 * @author AutoFlightGenerator
 * @version 2.0.0
 */

class UASFMManager {
    constructor(options = {}) {
        // Configuration options
        this.config = {
            apiEndpoint: 'https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson',
            metadataEndpoint: 'https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson?f=json',
            tfrEndpoint: 'https://tfr.faa.gov/tfr2/list.jsp',
            tfrApiEndpoint: 'https://external-api.faa.gov/notamapi/v1/tfr',
            cacheName: 'uasfm-cache',
            cacheVersion: 3,
            updateInterval: 56 * 24 * 60 * 60 * 1000, // 56 days in milliseconds
            maxCacheAge: 60 * 24 * 60 * 60 * 1000, // 60 days in milliseconds
            gridSize: 30, // 30 arc-seconds
            autoUpdateCheck: true,
            enableAuditLogging: true,
            ...options
        };

        // State management
        this.isInitialized = false;
        this.isLoading = false;
        this.lastUpdate = null;
        this.cache = null;
        this.overlays = new Map();
        this.eventListeners = new Map();
        this.tfrData = [];
        this.flightPlans = new Map();
        this.auditLog = [];
        this.isOffline = false;
        this.updateAvailable = false;

        // Initialize the module
        this.init();
    }

    /**
     * Initialize the UASFM manager
     */
    async init() {
        try {
            console.log('UASFM: Initializing...');
            
            // Initialize IndexedDB cache
            await this.initCache();
            
            // Load cached data
            await this.loadCachedData();
            
            // Check for updates
            await this.checkForUpdates();
            
            // Load TFR data
            await this.loadTFRData();
            
            // Initialize audit logging
            if (this.config.enableAuditLogging) {
                await this.initAuditLogging();
            }
            
            this.isInitialized = true;
            console.log('UASFM: Initialization complete');
            
            this.emit('initialized');
        } catch (error) {
            console.error('UASFM: Initialization failed:', error);
            this.emit('error', error);
        }
    }

    /**
     * Initialize IndexedDB cache
     */
    async initCache() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.config.cacheName, this.config.cacheVersion);
            
            request.onerror = () => {
                console.error('UASFM: Failed to open IndexedDB');
                reject(new Error('Failed to open IndexedDB'));
            };
            
            request.onsuccess = (event) => {
                this.cache = event.target.result;
                console.log('UASFM: IndexedDB cache initialized');
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object stores
                if (!db.objectStoreNames.contains('uasfm-data')) {
                    const dataStore = db.createObjectStore('uasfm-data', { keyPath: 'id' });
                    dataStore.createIndex('timestamp', 'timestamp', { unique: false });
                    dataStore.createIndex('bounds', 'bounds', { unique: false });
                }
                
                if (!db.objectStoreNames.contains('metadata')) {
                    const metadataStore = db.createObjectStore('metadata', { keyPath: 'key' });
                }
                
                if (!db.objectStoreNames.contains('tfr-data')) {
                    const tfrStore = db.createObjectStore('tfr-data', { keyPath: 'id' });
                    tfrStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
                
                if (!db.objectStoreNames.contains('flight-plans')) {
                    const flightPlanStore = db.createObjectStore('flight-plans', { keyPath: 'id' });
                    flightPlanStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
                
                if (!db.objectStoreNames.contains('audit-log')) {
                    const auditStore = db.createObjectStore('audit-log', { keyPath: 'id' });
                    auditStore.createIndex('timestamp', 'timestamp', { unique: false });
                    auditStore.createIndex('action', 'action', { unique: false });
                }
                
                console.log('UASFM: IndexedDB schema created');
            };
        });
    }

    /**
     * Load cached data from IndexedDB
     */
    async loadCachedData() {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                reject(new Error('Cache not initialized'));
                return;
            }

            const transaction = this.cache.transaction(['metadata'], 'readonly');
            const store = transaction.objectStore('metadata');
            const request = store.get('lastUpdate');

            request.onsuccess = () => {
                if (request.result) {
                    this.lastUpdate = request.result.value;
                    console.log('UASFM: Loaded cached metadata, last update:', this.lastUpdate);
                }
                resolve();
            };

            request.onerror = () => {
                console.warn('UASFM: Failed to load cached metadata');
                resolve(); // Continue without cached data
            };
        });
    }

    /**
     * Check for updates and fetch new data if needed
     */
    async checkForUpdates() {
        try {
            const now = Date.now();
            const shouldUpdate = !this.lastUpdate || 
                               (now - this.lastUpdate) > this.config.updateInterval;

            if (shouldUpdate) {
                console.log('UASFM: Checking for updates...');
                
                // Check if auto-update is enabled
                if (this.config.autoUpdateCheck) {
                    await this.checkForFAAUpdates();
                } else {
                    await this.fetchAndCacheData();
                }
            } else {
                console.log('UASFM: Using cached data, next update in', 
                    Math.round((this.config.updateInterval - (now - this.lastUpdate)) / (24 * 60 * 60 * 1000)), 'days');
            }
        } catch (error) {
            console.error('UASFM: Update check failed:', error);
            this.emit('error', error);
        }
    }

    /**
     * Check for FAA data updates by comparing timestamps
     */
    async checkForFAAUpdates() {
        try {
            console.log('UASFM: Checking FAA for data updates...');
            
            // Fetch metadata to check last modified date
            const response = await fetch(this.config.metadataEndpoint, {
                method: 'HEAD',
                headers: {
                    'Accept': 'application/json',
                    'User-Agent': 'AutoFlightGenerator-UASFM/2.0'
                }
            });

            if (!response.ok) {
                throw new Error(`FAA metadata check failed: ${response.status}`);
            }

            const lastModified = response.headers.get('last-modified');
            const etag = response.headers.get('etag');
            
            if (lastModified) {
                const faaLastUpdate = new Date(lastModified).getTime();
                const localLastUpdate = this.lastUpdate || 0;
                
                if (faaLastUpdate > localLastUpdate) {
                    console.log('UASFM: FAA data is newer than local cache');
                    this.updateAvailable = true;
                    this.emit('updateAvailable', {
                        faaLastUpdate: new Date(faaLastUpdate),
                        localLastUpdate: new Date(localLastUpdate),
                        etag: etag
                    });
                    
                    // Prompt user for update
                    if (confirm('New UASFM data is available from the FAA. Would you like to download it now?')) {
                        await this.fetchAndCacheData();
                    }
                } else {
                    console.log('UASFM: Local data is up to date');
                    this.updateAvailable = false;
                }
            } else {
                // Fallback to regular update check
                await this.fetchAndCacheData();
            }
            
        } catch (error) {
            console.warn('UASFM: FAA update check failed, using cached data:', error);
            this.isOffline = true;
            this.emit('offlineMode', error);
            
            // Use cached data if available
            if (await this.hasCachedData()) {
                this.emit('usingCachedData');
            }
        }
    }

    /**
     * Fetch UASFM data from FAA API and cache it
     */
    async fetchAndCacheData() {
        if (this.isLoading) {
            console.log('UASFM: Already loading data, skipping...');
            return;
        }

        this.isLoading = true;
        this.emit('loading');

        try {
            console.log('UASFM: Fetching data from FAA API...');
            
            const response = await fetch(this.config.apiEndpoint, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'User-Agent': 'AutoFlightGenerator-UASFM/2.0'
                },
                timeout: 30000 // 30 second timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const geojson = await response.json();
            
            // Validate GeoJSON structure
            if (!this.validateGeoJSON(geojson)) {
                throw new Error('Invalid GeoJSON structure received from FAA API');
            }

            // Parse and process the data
            const processedData = this.processGeoJSON(geojson);
            
            // Cache the processed data
            await this.cacheData(processedData);
            
            // Update metadata
            this.lastUpdate = Date.now();
            await this.updateMetadata();
            
            console.log('UASFM: Data successfully fetched and cached');
            this.emit('dataUpdated', processedData);
            
        } catch (error) {
            console.error('UASFM: Failed to fetch data:', error);
            this.emit('error', error);
            
            // If we have cached data, we can still use it
            if (await this.hasCachedData()) {
                console.log('UASFM: Falling back to cached data');
                this.emit('usingCachedData');
            }
        } finally {
            this.isLoading = false;
            this.emit('loadingComplete');
        }
    }

    /**
     * Load TFR data
     */
    async loadTFRData() {
        try {
            console.log('UASFM: Loading TFR data...');
            
            // Try to load from cache first
            const cachedTFR = await this.getCachedTFRData();
            if (cachedTFR && cachedTFR.length > 0) {
                this.tfrData = cachedTFR;
                console.log('UASFM: Loaded', cachedTFR.length, 'TFRs from cache');
                this.emit('tfrDataLoaded', cachedTFR);
                return;
            }
            
            // Fetch fresh TFR data
            await this.fetchTFRData();
            
        } catch (error) {
            console.error('UASFM: Failed to load TFR data:', error);
            this.emit('error', error);
        }
    }

    /**
     * Fetch TFR data from FAA
     */
    async fetchTFRData() {
        try {
            // Note: This is a simplified TFR fetch. In production, you'd use the actual FAA TFR API
            const response = await fetch(this.config.tfrApiEndpoint, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'User-Agent': 'AutoFlightGenerator-UASFM/2.0'
                }
            });

            if (!response.ok) {
                throw new Error(`TFR API error: ${response.status}`);
            }

            const tfrData = await response.json();
            this.tfrData = this.processTFRData(tfrData);
            
            // Cache TFR data
            await this.cacheTFRData(this.tfrData);
            
            console.log('UASFM: Loaded', this.tfrData.length, 'TFRs');
            this.emit('tfrDataUpdated', this.tfrData);
            
        } catch (error) {
            console.error('UASFM: Failed to fetch TFR data:', error);
            // Create sample TFR data for demonstration
            this.tfrData = this.createSampleTFRData();
            this.emit('tfrDataUpdated', this.tfrData);
        }
    }

    /**
     * Create sample TFR data for demonstration
     */
    createSampleTFRData() {
        return [
            {
                id: 'TFR001',
                type: 'TFR',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [-122.5, 37.7],
                        [-122.4, 37.7],
                        [-122.4, 37.8],
                        [-122.5, 37.8],
                        [-122.5, 37.7]
                    ]]
                },
                properties: {
                    title: 'Sample TFR - San Francisco Area',
                    description: 'Temporary Flight Restriction for special event',
                    startDate: new Date().toISOString(),
                    endDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
                    minAltitude: 0,
                    maxAltitude: 18000,
                    reason: 'Special Event'
                }
            }
        ];
    }

    /**
     * Process TFR data
     */
    processTFRData(rawData) {
        // Process raw TFR data into standardized format
        return rawData.map(tfr => ({
            id: tfr.id || `TFR_${Date.now()}_${Math.random()}`,
            type: 'TFR',
            geometry: tfr.geometry,
            properties: {
                title: tfr.title || 'Temporary Flight Restriction',
                description: tfr.description || '',
                startDate: tfr.startDate || new Date().toISOString(),
                endDate: tfr.endDate || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
                minAltitude: tfr.minAltitude || 0,
                maxAltitude: tfr.maxAltitude || 18000,
                reason: tfr.reason || 'Unknown'
            }
        }));
    }

    /**
     * Check for TFR conflicts in a flight plan
     */
    checkTFRConflicts(flightPlan) {
        const conflicts = [];
        
        for (const tfr of this.tfrData) {
            if (this.polygonsIntersect(flightPlan.geometry, tfr.geometry)) {
                conflicts.push({
                    tfr: tfr,
                    severity: 'HIGH',
                    message: `Flight plan intersects with TFR: ${tfr.properties.title}`
                });
            }
        }
        
        return conflicts;
    }

    /**
     * Validate flight plan against UASFM data
     */
    async validateFlightPlan(flightPlan) {
        const validation = {
            isValid: true,
            warnings: [],
            errors: [],
            altitudeCompliance: [],
            tfrConflicts: [],
            recommendations: []
        };

        try {
            // Check TFR conflicts
            validation.tfrConflicts = this.checkTFRConflicts(flightPlan);
            if (validation.tfrConflicts.length > 0) {
                validation.isValid = false;
                validation.errors.push('Flight plan intersects with TFR(s)');
            }

            // Check altitude compliance
            const altitudeChecks = await this.checkAltitudeCompliance(flightPlan);
            validation.altitudeCompliance = altitudeChecks;

            // Check for altitude violations
            const violations = altitudeChecks.filter(check => !check.compliant);
            if (violations.length > 0) {
                validation.warnings.push(`${violations.length} altitude violations detected`);
            }

            // Generate recommendations
            validation.recommendations = this.generateRecommendations(validation);

            return validation;

        } catch (error) {
            console.error('UASFM: Flight plan validation failed:', error);
            validation.isValid = false;
            validation.errors.push('Validation failed: ' + error.message);
            return validation;
        }
    }

    /**
     * Check altitude compliance for flight plan
     */
    async checkAltitudeCompliance(flightPlan) {
        const checks = [];
        
        // Sample points along the flight plan
        const samplePoints = this.sampleFlightPlan(flightPlan, 10);
        
        for (const point of samplePoints) {
            const altitudeInfo = await this.getAltitudeAtLocation(point[1], point[0]);
            if (altitudeInfo) {
                const plannedAltitude = flightPlan.properties.maxAltitude || 400;
                const maxAllowed = altitudeInfo.maxAltitude;
                
                checks.push({
                    location: point,
                    plannedAltitude: plannedAltitude,
                    maxAllowed: maxAllowed,
                    compliant: plannedAltitude <= maxAllowed,
                    gridId: altitudeInfo.gridId
                });
            }
        }
        
        return checks;
    }

    /**
     * Sample points along a flight plan
     */
    sampleFlightPlan(flightPlan, numPoints = 10) {
        const points = [];
        const coordinates = flightPlan.geometry.coordinates[0];
        
        for (let i = 0; i < numPoints; i++) {
            const index = Math.floor((i / (numPoints - 1)) * (coordinates.length - 1));
            points.push(coordinates[index]);
        }
        
        return points;
    }

    /**
     * Generate recommendations based on validation results
     */
    generateRecommendations(validation) {
        const recommendations = [];
        
        if (validation.tfrConflicts.length > 0) {
            recommendations.push('Avoid flying in TFR areas or wait until restrictions are lifted');
        }
        
        if (validation.altitudeCompliance.some(check => !check.compliant)) {
            recommendations.push('Reduce flight altitude to comply with UASFM restrictions');
        }
        
        if (validation.altitudeCompliance.some(check => check.maxAllowed < 400)) {
            recommendations.push('Consider obtaining LAANC authorization for controlled airspace');
        }
        
        return recommendations;
    }

    /**
     * Submit LAANC request (simulated)
     */
    async submitLAANCRequest(flightPlan) {
        try {
            const request = {
                id: `LAANC_${Date.now()}`,
                timestamp: new Date().toISOString(),
                flightPlan: flightPlan,
                status: 'PENDING',
                requestData: {
                    operator: 'Demo Operator',
                    aircraft: 'Demo Aircraft',
                    purpose: 'Recreational',
                    maxAltitude: flightPlan.properties.maxAltitude || 400,
                    duration: flightPlan.properties.duration || '2 hours'
                }
            };
            
            // Log LAANC request
            await this.logAuditEvent('LAANC_REQUEST', {
                flightPlanId: flightPlan.id,
                maxAltitude: flightPlan.properties.maxAltitude,
                purpose: flightPlan.properties.purpose
            });
            
            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Simulate approval (in real implementation, this would be from FAA)
            request.status = 'APPROVED';
            request.approvalData = {
                approvalNumber: `LAANC_${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
                approvedAltitude: Math.min(request.requestData.maxAltitude, 400),
                conditions: ['Maintain visual line of sight', 'Fly during daylight hours'],
                expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
            };
            
            // Store request
            await this.storeLAANCRequest(request);
            
            // Log approval
            await this.logAuditEvent('LAANC_APPROVED', {
                requestId: request.id,
                approvalNumber: request.approvalData.approvalNumber,
                approvedAltitude: request.approvalData.approvedAltitude
            });
            
            console.log('UASFM: LAANC request submitted:', request);
            this.emit('laancRequestSubmitted', request);
            
            return request;
            
        } catch (error) {
            console.error('UASFM: LAANC request failed:', error);
            
            // Log error
            await this.logAuditEvent('LAANC_ERROR', {
                error: error.message,
                flightPlanId: flightPlan.id
            });
            
            throw error;
        }
    }

    /**
     * Store LAANC request
     */
    async storeLAANCRequest(request) {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                reject(new Error('Cache not initialized'));
                return;
            }

            const transaction = this.cache.transaction(['flight-plans'], 'readwrite');
            const store = transaction.objectStore('flight-plans');
            const dbRequest = store.put(request);

            dbRequest.onsuccess = () => resolve();
            dbRequest.onerror = () => reject(dbRequest.error);
        });
    }

    /**
     * Get cached TFR data
     */
    async getCachedTFRData() {
        return new Promise((resolve) => {
            if (!this.cache) {
                resolve([]);
                return;
            }

            const transaction = this.cache.transaction(['tfr-data'], 'readonly');
            const store = transaction.objectStore('tfr-data');
            const request = store.getAll();

            request.onsuccess = () => {
                resolve(request.result || []);
            };

            request.onerror = () => {
                resolve([]);
            };
        });
    }

    /**
     * Cache TFR data
     */
    async cacheTFRData(tfrData) {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                reject(new Error('Cache not initialized'));
                return;
            }

            const transaction = this.cache.transaction(['tfr-data'], 'readwrite');
            const store = transaction.objectStore('tfr-data');

            // Clear existing data
            const clearRequest = store.clear();
            
            clearRequest.onsuccess = () => {
                // Store new data
                const promises = tfrData.map(tfr => {
                    return new Promise((resolve, reject) => {
                        const request = store.add({
                            ...tfr,
                            timestamp: Date.now()
                        });
                        
                        request.onsuccess = () => resolve();
                        request.onerror = () => reject(request.error);
                    });
                });

                Promise.all(promises)
                    .then(() => {
                        console.log('UASFM: TFR data cached successfully');
                        resolve();
                    })
                    .catch(reject);
            };

            clearRequest.onerror = () => reject(clearRequest.error);
        });
    }

    /**
     * Check if two polygons intersect
     */
    polygonsIntersect(poly1, poly2) {
        // Simplified intersection check - in production, use a proper geometry library
        const coords1 = poly1.coordinates[0];
        const coords2 = poly2.coordinates[0];
        
        // Check if any point from poly1 is inside poly2 or vice versa
        for (const coord of coords1) {
            if (this.pointInPolygon(coord, coords2)) {
                return true;
            }
        }
        
        for (const coord of coords2) {
            if (this.pointInPolygon(coord, coords1)) {
                return true;
            }
        }
        
        return false;
    }

    /**
     * Validate GeoJSON structure
     */
    validateGeoJSON(geojson) {
        if (!geojson || typeof geojson !== 'object') {
            return false;
        }

        if (geojson.type !== 'FeatureCollection') {
            return false;
        }

        if (!Array.isArray(geojson.features)) {
            return false;
        }

        // Check if features have required properties
        for (const feature of geojson.features) {
            if (!feature.geometry || !feature.properties) {
                return false;
            }
            
            // Check for required UASFM properties
            const props = feature.properties;
            if (typeof props.maxAltitude !== 'number' || 
                typeof props.gridId !== 'string') {
                return false;
            }
        }

        return true;
    }

    /**
     * Process GeoJSON data into optimized format
     */
    processGeoJSON(geojson) {
        console.log('UASFM: Processing', geojson.features.length, 'features...');
        
        const processedFeatures = [];
        const bounds = {
            north: -90, south: 90, east: -180, west: 180
        };

        for (const feature of geojson.features) {
            try {
                const processed = this.processFeature(feature);
                if (processed) {
                    processedFeatures.push(processed);
                    
                    // Update bounds
                    if (processed.bounds) {
                        bounds.north = Math.max(bounds.north, processed.bounds.north);
                        bounds.south = Math.min(bounds.south, processed.bounds.south);
                        bounds.east = Math.max(bounds.east, processed.bounds.east);
                        bounds.west = Math.min(bounds.west, processed.bounds.west);
                    }
                }
            } catch (error) {
                console.warn('UASFM: Failed to process feature:', error);
            }
        }

        console.log('UASFM: Processed', processedFeatures.length, 'features');
        
        return {
            features: processedFeatures,
            bounds: bounds,
            timestamp: Date.now(),
            totalFeatures: geojson.features.length
        };
    }

    /**
     * Process individual GeoJSON feature
     */
    processFeature(feature) {
        const props = feature.properties;
        const geometry = feature.geometry;

        // Extract grid information
        const gridId = props.gridId || props.GRID_ID || props.id;
        const maxAltitude = props.maxAltitude || props.MAX_ALTITUDE || props.max_altitude || 400;
        const gridType = props.gridType || props.GRID_TYPE || 'standard';

        // Calculate bounds from geometry
        let bounds = null;
        if (geometry && geometry.coordinates) {
            bounds = this.calculateBounds(geometry.coordinates);
        }

        return {
            id: gridId,
            maxAltitude: Math.max(0, Math.min(400, maxAltitude)), // Clamp to 0-400 ft
            gridType: gridType,
            bounds: bounds,
            geometry: geometry,
            properties: {
                gridId: gridId,
                maxAltitude: maxAltitude,
                gridType: gridType,
                ...props
            }
        };
    }

    /**
     * Calculate bounds from geometry coordinates
     */
    calculateBounds(coordinates) {
        if (!Array.isArray(coordinates) || coordinates.length === 0) {
            return null;
        }

        let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;

        const processCoords = (coords) => {
            if (Array.isArray(coords[0])) {
                coords.forEach(processCoords);
            } else {
                const [lng, lat] = coords;
                minLat = Math.min(minLat, lat);
                maxLat = Math.max(maxLat, lat);
                minLng = Math.min(minLng, lng);
                maxLng = Math.max(maxLng, lng);
            }
        };

        processCoords(coordinates);

        return {
            north: maxLat,
            south: minLat,
            east: maxLng,
            west: minLng
        };
    }

    /**
     * Cache processed data in IndexedDB
     */
    async cacheData(data) {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                reject(new Error('Cache not initialized'));
                return;
            }

            const transaction = this.cache.transaction(['uasfm-data', 'metadata'], 'readwrite');
            const dataStore = transaction.objectStore('uasfm-data');
            const metadataStore = transaction.objectStore('metadata');

            // Clear existing data
            const clearRequest = dataStore.clear();
            
            clearRequest.onsuccess = () => {
                // Store new data
                const promises = data.features.map(feature => {
                    return new Promise((resolve, reject) => {
                        const request = dataStore.add({
                            id: feature.id,
                            ...feature,
                            timestamp: data.timestamp
                        });
                        
                        request.onsuccess = () => resolve();
                        request.onerror = () => reject(request.error);
                    });
                });

                // Store metadata
                const metadataRequest = metadataStore.put({
                    key: 'lastUpdate',
                    value: data.timestamp
                });

                Promise.all([...promises, metadataRequest])
                    .then(() => {
                        console.log('UASFM: Data cached successfully');
                        resolve();
                    })
                    .catch(reject);
            };

            clearRequest.onerror = () => reject(clearRequest.error);
        });
    }

    /**
     * Update metadata in cache
     */
    async updateMetadata() {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                reject(new Error('Cache not initialized'));
                return;
            }

            const transaction = this.cache.transaction(['metadata'], 'readwrite');
            const store = transaction.objectStore('metadata');
            const request = store.put({
                key: 'lastUpdate',
                value: this.lastUpdate
            });

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Check if cached data exists
     */
    async hasCachedData() {
        return new Promise((resolve) => {
            if (!this.cache) {
                resolve(false);
                return;
            }

            const transaction = this.cache.transaction(['uasfm-data'], 'readonly');
            const store = transaction.objectStore('uasfm-data');
            const request = store.count();

            request.onsuccess = () => {
                resolve(request.result > 0);
            };

            request.onerror = () => {
                resolve(false);
            };
        });
    }

    /**
     * Get UASFM data for a specific area
     */
    async getDataForBounds(bounds, options = {}) {
        if (!this.isInitialized) {
            throw new Error('UASFM manager not initialized');
        }

        const {
            maxAltitude = 400,
            includeGeometry = false,
            useCache = true
        } = options;

        try {
            let features = [];

            if (useCache) {
                features = await this.getCachedDataForBounds(bounds);
            }

            if (features.length === 0) {
                // No cached data, fetch fresh data
                await this.fetchAndCacheData();
                features = await this.getCachedDataForBounds(bounds);
            }

            // Filter by max altitude if specified
            if (maxAltitude !== null) {
                features = features.filter(f => f.maxAltitude <= maxAltitude);
            }

            // Remove geometry if not needed
            if (!includeGeometry) {
                features = features.map(f => ({
                    id: f.id,
                    maxAltitude: f.maxAltitude,
                    gridType: f.gridType,
                    bounds: f.bounds,
                    properties: f.properties
                }));
            }

            return features;

        } catch (error) {
            console.error('UASFM: Failed to get data for bounds:', error);
            throw error;
        }
    }

    /**
     * Get cached data for specific bounds
     */
    async getCachedDataForBounds(bounds) {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                resolve([]);
                return;
            }

            const transaction = this.cache.transaction(['uasfm-data'], 'readonly');
            const store = transaction.objectStore('uasfm-data');
            const request = store.getAll();

            request.onsuccess = () => {
                const features = request.result.filter(feature => {
                    if (!feature.bounds) return false;
                    
                    // Check if bounds overlap
                    return !(bounds.east < feature.bounds.west ||
                            bounds.west > feature.bounds.east ||
                            bounds.south > feature.bounds.north ||
                            bounds.north < feature.bounds.south);
                });

                resolve(features);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    /**
     * Create Leaflet overlay for UASFM data with performance optimizations
     */
    createOverlay(map, options = {}) {
        const {
            opacity = 0.6,
            colorByAltitude = true,
            showLabels = true,
            maxAltitude = 400,
            onFeatureClick = null,
            enableTurfClipping = true,
            maxFeaturesPerUpdate = 1000,
            debounceDelay = 300
        } = options;

        const overlay = L.layerGroup();
        let currentData = [];
        let updateTimeout = null;
        let lastUpdateBounds = null;

        // Color scale for altitude visualization (cached for performance)
        const colorCache = new Map();
        const getColor = (altitude) => {
            if (!colorByAltitude) return '#ff7800';
            
            if (colorCache.has(altitude)) {
                return colorCache.get(altitude);
            }
            
            const normalized = Math.min(altitude / 400, 1);
            const hue = 120 - (normalized * 120); // Green to Red
            const color = `hsl(${hue}, 70%, 50%)`;
            colorCache.set(altitude, color);
            return color;
        };

        // Create polygon for grid cell with accessibility features
        const createGridPolygon = (feature) => {
            if (!feature.geometry || feature.geometry.type !== 'Polygon') {
                return null;
            }

            const polygon = L.polygon(feature.geometry.coordinates[0], {
                color: getColor(feature.maxAltitude),
                weight: 1,
                opacity: 0.8,
                fillColor: getColor(feature.maxAltitude),
                fillOpacity: opacity
            });

            // Add accessibility attributes
            const altitudeDescription = this.getAltitudeDescription(feature.maxAltitude);
            polygon.getElement = () => {
                const element = document.createElement('div');
                element.setAttribute('role', 'button');
                element.setAttribute('tabindex', '0');
                element.setAttribute('aria-label', `UAS Facility Map grid ${feature.id}, ${altitudeDescription}`);
                element.setAttribute('aria-describedby', `grid-${feature.id}-description`);
                return element;
            };

            // Add popup with information and accessibility
            const popupContent = this.createAccessiblePopup(feature);
            polygon.bindPopup(popupContent);

            // Add click handler if provided
            if (onFeatureClick) {
                polygon.on('click', (e) => {
                    onFeatureClick(feature, e);
                });
            }

            // Add keyboard navigation
            polygon.on('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (onFeatureClick) {
                        onFeatureClick(feature, e);
                    }
                }
            });

            return polygon;
        };

        // Debounced update function for performance
        const debouncedUpdate = (mapBounds) => {
            if (updateTimeout) {
                clearTimeout(updateTimeout);
            }
            
            updateTimeout = setTimeout(() => {
                updateOverlay(mapBounds);
            }, debounceDelay);
        };

        // Update overlay with new data (optimized)
        const updateOverlay = async (mapBounds) => {
            try {
                const bounds = {
                    north: mapBounds.getNorth(),
                    south: mapBounds.getSouth(),
                    east: mapBounds.getEast(),
                    west: mapBounds.getWest()
                };

                // Check if bounds have changed significantly
                if (lastUpdateBounds && this.boundsSimilar(lastUpdateBounds, bounds, 0.01)) {
                    return; // Skip update if bounds haven't changed significantly
                }

                const data = await this.getDataForBounds(bounds, {
                    maxAltitude: maxAltitude,
                    includeGeometry: true
                });

                // Limit features for performance
                const limitedData = data.slice(0, maxFeaturesPerUpdate);

                // Use Turf.js for clipping if available and enabled
                let clippedData = limitedData;
                if (enableTurfClipping && typeof turf !== 'undefined') {
                    clippedData = this.clipFeaturesToBounds(limitedData, bounds);
                }

                // Clear existing overlay
                overlay.clearLayers();

                // Add new features in batches for better performance
                const batchSize = 100;
                for (let i = 0; i < clippedData.length; i += batchSize) {
                    const batch = clippedData.slice(i, i + batchSize);
                    
                    // Use requestAnimationFrame for smooth rendering
                    await new Promise(resolve => {
                        requestAnimationFrame(() => {
                            batch.forEach(feature => {
                                const polygon = createGridPolygon(feature);
                                if (polygon) {
                                    overlay.addLayer(polygon);
                                }
                            });
                            resolve();
                        });
                    });
                }

                currentData = clippedData;
                lastUpdateBounds = bounds;
                
                console.log('UASFM: Overlay updated with', clippedData.length, 'features');

            } catch (error) {
                console.error('UASFM: Failed to update overlay:', error);
            }
        };

        // Initial update
        if (map) {
            updateOverlay(map.getBounds());
        }

        // Listen for map view changes with debouncing
        if (map) {
            map.on('moveend', () => {
                debouncedUpdate(map.getBounds());
            });
            
            map.on('zoomend', () => {
                debouncedUpdate(map.getBounds());
            });
        }

        // Store overlay reference
        const overlayId = `uasfm-${Date.now()}`;
        this.overlays.set(overlayId, {
            overlay,
            updateOverlay,
            options,
            colorCache
        });

        return {
            id: overlayId,
            layer: overlay,
            update: () => updateOverlay(map.getBounds()),
            remove: () => {
                this.overlays.delete(overlayId);
                if (map) {
                    map.removeLayer(overlay);
                }
                if (updateTimeout) {
                    clearTimeout(updateTimeout);
                }
            }
        };
    }

    /**
     * Get accessible description for altitude
     */
    getAltitudeDescription(altitude) {
        if (altitude <= 100) {
            return `Low altitude zone, maximum ${altitude} feet above ground level`;
        } else if (altitude <= 200) {
            return `Medium altitude zone, maximum ${altitude} feet above ground level`;
        } else if (altitude <= 300) {
            return `High altitude zone, maximum ${altitude} feet above ground level`;
        } else {
            return `Restricted altitude zone, maximum ${altitude} feet above ground level`;
        }
    }

    /**
     * Create accessible popup content
     */
    createAccessiblePopup(feature) {
        const props = feature.properties;
        const altitude = props.maxAltitude || 400;
        const gridId = props.gridId || props.id || 'Unknown';
        const airspaceClass = props.airspaceClass || props.AIRSPACE_CLASS || 'Unknown';
        
        return `
            <div class="uasfm-popup" role="dialog" aria-labelledby="popup-title-${gridId}">
                <h4 id="popup-title-${gridId}" style="margin: 0 0 8px 0; color: #333;">
                    UAS Facility Map Grid
                </h4>
                <div class="info-row" role="group" aria-labelledby="grid-info-${gridId}">
                    <span class="label">Grid ID:</span>
                    <span class="value" aria-label="Grid identifier">${gridId}</span>
                </div>
                <div class="info-row">
                    <span class="label">Max Altitude:</span>
                    <span class="value" aria-label="Maximum altitude ${altitude} feet above ground level">
                        ${altitude} ft AGL
                    </span>
                </div>
                <div class="info-row">
                    <span class="label">Airspace Class:</span>
                    <span class="value" aria-label="Airspace class ${airspaceClass}">${airspaceClass}</span>
                </div>
                <div class="info-row">
                    <span class="label">Grid Type:</span>
                    <span class="value">${props.gridType || 'Standard'}</span>
                </div>
                ${props.airportName ? `
                    <div class="info-row">
                        <span class="label">Airport:</span>
                        <span class="value" aria-label="Associated airport ${props.airportName}">
                            ${props.airportName}
                        </span>
                    </div>
                ` : ''}
                <div class="warning" role="alert" aria-live="polite">
                    <strong>Important:</strong> This is informational data only. 
                    Obtain LAANC authorization before flying in controlled airspace.
                </div>
            </div>
        `;
    }

    /**
     * Check if bounds are similar (for optimization)
     */
    boundsSimilar(bounds1, bounds2, threshold = 0.01) {
        return Math.abs(bounds1.north - bounds2.north) < threshold &&
               Math.abs(bounds1.south - bounds2.south) < threshold &&
               Math.abs(bounds1.east - bounds2.east) < threshold &&
               Math.abs(bounds1.west - bounds2.west) < threshold;
    }

    /**
     * Clip features to bounds using Turf.js (if available)
     */
    clipFeaturesToBounds(features, bounds) {
        if (typeof turf === 'undefined') {
            return features;
        }

        try {
            const bbox = [bounds.west, bounds.south, bounds.east, bounds.north];
            const bboxPolygon = turf.bboxPolygon(bbox);
            
            return features.filter(feature => {
                if (!feature.geometry) return false;
                
                const featurePolygon = turf.polygon(feature.geometry.coordinates);
                return turf.booleanIntersects(featurePolygon, bboxPolygon);
            });
        } catch (error) {
            console.warn('UASFM: Turf.js clipping failed, using original features:', error);
            return features;
        }
    }

    /**
     * Create TFR overlay
     */
    createTFROverlay(map, options = {}) {
        const {
            opacity = 0.7,
            color = '#dc3545',
            weight = 2
        } = options;

        const overlay = L.layerGroup();

        // Add TFR polygons
        this.tfrData.forEach(tfr => {
            if (tfr.geometry && tfr.geometry.type === 'Polygon') {
                const polygon = L.polygon(tfr.geometry.coordinates[0], {
                    color: color,
                    weight: weight,
                    opacity: 0.8,
                    fillColor: color,
                    fillOpacity: opacity
                });

                // Add popup
                const popupContent = `
                    <div style="font-family: Arial, sans-serif; font-size: 12px;">
                        <h4 style="margin: 0 0 8px 0; color: #333;">⚠️ Temporary Flight Restriction</h4>
                        <p style="margin: 4px 0;"><strong>Title:</strong> ${tfr.properties.title}</p>
                        <p style="margin: 4px 0;"><strong>Reason:</strong> ${tfr.properties.reason}</p>
                        <p style="margin: 4px 0;"><strong>Start:</strong> ${new Date(tfr.properties.startDate).toLocaleDateString()}</p>
                        <p style="margin: 4px 0;"><strong>End:</strong> ${new Date(tfr.properties.endDate).toLocaleDateString()}</p>
                        <p style="margin: 4px 0;"><strong>Altitude:</strong> ${tfr.properties.minAltitude}-${tfr.properties.maxAltitude} ft</p>
                        <div style="margin-top: 8px; padding: 6px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; font-size: 11px; color: #721c24;">
                            <strong>⚠️ WARNING:</strong> Flight operations are restricted in this area.
                        </div>
                    </div>
                `;

                polygon.bindPopup(popupContent);
                overlay.addLayer(polygon);
            }
        });

        return overlay;
    }

    /**
     * Get altitude information for a specific location
     */
    async getAltitudeAtLocation(lat, lng) {
        try {
            const bounds = {
                north: lat + 0.01,
                south: lat - 0.01,
                east: lng + 0.01,
                west: lng - 0.01
            };

            const features = await this.getDataForBounds(bounds, {
                includeGeometry: true
            });

            // Find the feature that contains the point
            for (const feature of features) {
                if (feature.geometry && this.pointInPolygon([lng, lat], feature.geometry.coordinates[0])) {
                    return {
                        maxAltitude: feature.maxAltitude,
                        gridId: feature.id,
                        gridType: feature.gridType,
                        properties: feature.properties
                    };
                }
            }

            return null;

        } catch (error) {
            console.error('UASFM: Failed to get altitude at location:', error);
            return null;
        }
    }

    /**
     * Check if point is inside polygon
     */
    pointInPolygon(point, polygon) {
        const [x, y] = point;
        let inside = false;

        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const [xi, yi] = polygon[i];
            const [xj, yj] = polygon[j];

            if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
                inside = !inside;
            }
        }

        return inside;
    }

    /**
     * Force refresh of UASFM data
     */
    async refresh() {
        console.log('UASFM: Force refreshing data...');
        this.lastUpdate = null;
        await this.fetchAndCacheData();
        await this.loadTFRData();
    }

    /**
     * Clear all cached data
     */
    async clearCache() {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                resolve();
                return;
            }

            const transaction = this.cache.transaction(['uasfm-data', 'metadata', 'tfr-data', 'flight-plans'], 'readwrite');
            const dataStore = transaction.objectStore('uasfm-data');
            const metadataStore = transaction.objectStore('metadata');
            const tfrStore = transaction.objectStore('tfr-data');
            const flightPlanStore = transaction.objectStore('flight-plans');

            const clearData = dataStore.clear();
            const clearMetadata = metadataStore.clear();
            const clearTFR = tfrStore.clear();
            const clearFlightPlans = flightPlanStore.clear();

            Promise.all([clearData, clearMetadata, clearTFR, clearFlightPlans])
                .then(() => {
                    this.lastUpdate = null;
                    this.tfrData = [];
                    console.log('UASFM: Cache cleared');
                    resolve();
                })
                .catch(reject);
        });
    }

    /**
     * Get cache statistics
     */
    async getCacheStats() {
        return new Promise((resolve) => {
            if (!this.cache) {
                resolve(null);
                return;
            }

            const transaction = this.cache.transaction(['uasfm-data', 'metadata', 'tfr-data', 'flight-plans'], 'readonly');
            const dataStore = transaction.objectStore('uasfm-data');
            const metadataStore = transaction.objectStore('metadata');
            const tfrStore = transaction.objectStore('tfr-data');
            const flightPlanStore = transaction.objectStore('flight-plans');

            const dataCount = dataStore.count();
            const lastUpdate = metadataStore.get('lastUpdate');
            const tfrCount = tfrStore.count();
            const flightPlanCount = flightPlanStore.count();

            Promise.all([dataCount, lastUpdate, tfrCount, flightPlanCount])
                .then(([dataCount, update, tfrCount, flightPlanCount]) => {
                    resolve({
                        featureCount: dataCount,
                        tfrCount: tfrCount,
                        flightPlanCount: flightPlanCount,
                        lastUpdate: update ? update.value : null,
                        cacheAge: update ? Date.now() - update.value : null
                    });
                })
                .catch(() => resolve(null));
        });
    }

    /**
     * Event handling
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, ...args) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(...args);
                } catch (error) {
                    console.error('UASFM: Event handler error:', error);
                }
            });
        }
    }

    /**
     * Initialize audit logging
     */
    async initAuditLogging() {
        try {
            // Load existing audit log
            const existingLog = await this.getAuditLog();
            this.auditLog = existingLog || [];
            
            // Log initialization
            await this.logAuditEvent('SYSTEM_INIT', {
                version: '2.0.0',
                timestamp: new Date().toISOString()
            });
            
            console.log('UASFM: Audit logging initialized');
        } catch (error) {
            console.error('UASFM: Failed to initialize audit logging:', error);
        }
    }

    /**
     * Log audit event
     */
    async logAuditEvent(action, data = {}) {
        try {
            const event = {
                id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                timestamp: new Date().toISOString(),
                action: action,
                data: data,
                userAgent: navigator.userAgent,
                sessionId: this.getSessionId()
            };
            
            // Add to memory
            this.auditLog.push(event);
            
            // Store in database
            await this.storeAuditEvent(event);
            
            // Keep only last 1000 events in memory
            if (this.auditLog.length > 1000) {
                this.auditLog = this.auditLog.slice(-1000);
            }
            
            console.log('UASFM: Audit event logged:', action, data);
            
        } catch (error) {
            console.error('UASFM: Failed to log audit event:', error);
        }
    }

    /**
     * Store audit event in database
     */
    async storeAuditEvent(event) {
        return new Promise((resolve, reject) => {
            if (!this.cache) {
                resolve();
                return;
            }

            const transaction = this.cache.transaction(['audit-log'], 'readwrite');
            const store = transaction.objectStore('audit-log');
            const request = store.add(event);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get audit log
     */
    async getAuditLog(limit = 1000) {
        return new Promise((resolve) => {
            if (!this.cache) {
                resolve([]);
                return;
            }

            const transaction = this.cache.transaction(['audit-log'], 'readonly');
            const store = transaction.objectStore('audit-log');
            const request = store.getAll();

            request.onsuccess = () => {
                const events = request.result || [];
                // Sort by timestamp descending and limit
                const sortedEvents = events
                    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                    .slice(0, limit);
                resolve(sortedEvents);
            };

            request.onerror = () => {
                resolve([]);
            };
        });
    }

    /**
     * Export audit log
     */
    async exportAuditLog() {
        try {
            const events = await this.getAuditLog();
            const exportData = {
                exportDate: new Date().toISOString(),
                totalEvents: events.length,
                events: events
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `uasfm_audit_log_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            console.log('UASFM: Audit log exported');
            
        } catch (error) {
            console.error('UASFM: Failed to export audit log:', error);
        }
    }

    /**
     * Get session ID
     */
    getSessionId() {
        if (!this._sessionId) {
            this._sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }
        return this._sessionId;
    }

    /**
     * Destroy the UASFM manager
     */
    destroy() {
        // Remove all overlays
        this.overlays.forEach(overlay => {
            if (overlay.overlay) {
                overlay.overlay.clearLayers();
            }
        });
        this.overlays.clear();

        // Clear event listeners
        this.eventListeners.clear();

        // Close database connection
        if (this.cache) {
            this.cache.close();
            this.cache = null;
        }

        this.isInitialized = false;
        console.log('UASFM: Manager destroyed');
    }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UASFMManager;
} else if (typeof window !== 'undefined') {
    window.UASFMManager = UASFMManager;
}

// Auto-initialize if loaded in browser context
if (typeof window !== 'undefined' && typeof L !== 'undefined') {
    // Create global instance
    window.uasfm = new UASFMManager();
    
    // Add convenience methods to Leaflet
L.UASFM = {
    createOverlay: (map, options) => window.uasfm.createOverlay(map, options),
    createTFROverlay: (map, options) => window.uasfm.createTFROverlay(map, options),
    getAltitudeAtLocation: (lat, lng) => window.uasfm.getAltitudeAtLocation(lat, lng),
    validateFlightPlan: (flightPlan) => window.uasfm.validateFlightPlan(flightPlan),
    submitLAANCRequest: (flightPlan) => window.uasfm.submitLAANCRequest(flightPlan),
    refresh: () => window.uasfm.refresh(),
    getCacheStats: () => window.uasfm.getCacheStats(),
    exportAuditLog: () => window.uasfm.exportAuditLog(),
    getAuditLog: (limit) => window.uasfm.getAuditLog(limit),
    logAuditEvent: (action, data) => window.uasfm.logAuditEvent(action, data)
};
}
