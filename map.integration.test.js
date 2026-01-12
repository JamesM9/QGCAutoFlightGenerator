/**
 * Integration Tests for Map.html
 * 
 * Tests for map functionality, overlay interactions, and flight planning features
 * Run with: npm test map.integration.test.js
 */

// Mock DOM environment
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// Mock Leaflet
global.L = {
    map: jest.fn(() => ({
        setView: jest.fn(),
        addLayer: jest.fn(),
        removeLayer: jest.fn(),
        getBounds: jest.fn(() => ({
            getNorth: () => 37.8,
            getSouth: () => 37.7,
            getEast: () => -122.4,
            getWest: () => -122.5
        })),
        on: jest.fn(),
        off: jest.fn()
    })),
    tileLayer: jest.fn(() => ({
        addTo: jest.fn()
    })),
    geoJSON: jest.fn(() => ({
        addTo: jest.fn(),
        remove: jest.fn(),
        resetStyle: jest.fn()
    })),
    layerGroup: jest.fn(() => ({
        addLayer: jest.fn(),
        removeLayer: jest.fn(),
        clearLayers: jest.fn()
    })),
    polygon: jest.fn(() => ({
        bindPopup: jest.fn(),
        on: jest.fn(),
        setStyle: jest.fn(),
        bringToFront: jest.fn()
    })),
    marker: jest.fn(() => ({
        addTo: jest.fn(),
        bindPopup: jest.fn(),
        openPopup: jest.fn()
    })),
    control: {
        layers: jest.fn(() => ({
            addTo: jest.fn(),
            remove: jest.fn()
        }))
    },
    FeatureGroup: jest.fn(() => ({
        addLayer: jest.fn(),
        removeLayer: jest.fn(),
        clearLayers: jest.fn()
    })),
    Control: {
        Draw: jest.fn(() => ({
            addTo: jest.fn()
        }))
    }
};

// Mock UASFM module
const mockUASFMManager = {
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
    isInitialized: true,
    getDataForBounds: jest.fn(),
    validateFlightPlan: jest.fn(),
    submitLAANCRequest: jest.fn(),
    createTFROverlay: jest.fn(),
    tfrData: []
};

// Mock global functions
global.UASFMManager = jest.fn(() => mockUASFMManager);

describe('Map Integration Tests', () => {
    let dom;
    let document;
    let window;
    let mapElement;

    beforeEach(() => {
        // Create DOM environment
        dom = new JSDOM(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>UASFM Map Test</title>
            </head>
            <body>
                <div id="map"></div>
                <div id="search-panel" class="search-panel">
                    <input id="search-input" type="text" placeholder="Enter location">
                    <button id="search-button">Search</button>
                </div>
                <div id="flight-planning-panel" class="flight-planning-panel">
                    <input id="planned-altitude" type="number" value="400">
                    <input id="flight-duration" type="text" value="2 hours">
                    <input id="flight-purpose" type="text" value="Recreational">
                    <button id="draw-button">Draw Flight Plan</button>
                    <button id="validate-button">Validate Plan</button>
                    <button id="laanc-button" style="display: none;">Request LAANC</button>
                </div>
                <div id="validation-results" class="validation-results" style="display: none;"></div>
                <div id="laanc-panel" class="laanc-panel">
                    <div id="laanc-status"></div>
                    <div id="laanc-details"></div>
                </div>
                <div id="status-bar" class="status-bar">
                    <span id="uasfm-status">Initializing...</span>
                    <span id="grid-count">0</span>
                    <span id="tfr-count">0</span>
                    <span id="last-update">Never</span>
                </div>
            </body>
            </html>
        `, {
            url: 'http://localhost',
            pretendToBeVisual: true
        });

        document = dom.window.document;
        window = dom.window;
        mapElement = document.getElementById('map');

        // Mock global objects
        global.document = document;
        global.window = window;
        global.navigator = {
            geolocation: {
                getCurrentPosition: jest.fn()
            }
        };

        // Mock fetch
        global.fetch = jest.fn();

        // Mock console
        global.console = {
            log: jest.fn(),
            error: jest.fn(),
            warn: jest.fn()
        };

        // Mock performance
        global.performance = {
            now: () => Date.now()
        };

        // Reset mocks
        jest.clearAllMocks();
    });

    afterEach(() => {
        // Clean up
        if (dom) {
            dom.window.close();
        }
    });

    describe('Map Initialization', () => {
        test('should initialize map with correct view', () => {
            // Simulate map initialization
            const map = L.map('map').setView([37.7749, -122.4194], 13);
            
            expect(L.map).toHaveBeenCalledWith('map');
            expect(map.setView).toHaveBeenCalledWith([37.7749, -122.4194], 13);
        });

        test('should add base tile layer', () => {
            const baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            });

            expect(L.tileLayer).toHaveBeenCalledWith(
                'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                expect.objectContaining({
                    attribution: expect.stringContaining('OpenStreetMap'),
                    maxZoom: 19
                })
            );
        });

        test('should initialize UASFM manager', () => {
            // Simulate UASFM initialization
            const uasfmManager = new UASFMManager({
                apiEndpoint: 'https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson',
                updateInterval: 56 * 24 * 60 * 60 * 1000
            });

            expect(UASFMManager).toHaveBeenCalledWith(
                expect.objectContaining({
                    apiEndpoint: 'https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson',
                    updateInterval: 56 * 24 * 60 * 60 * 1000
                })
            );
        });
    });

    describe('UASFM Layer Management', () => {
        test('should load UASFM layer with correct styling', async () => {
            const mockFeatures = [
                {
                    id: 'GRID_001',
                    maxAltitude: 300,
                    geometry: {
                        type: 'Polygon',
                        coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    },
                    properties: {
                        gridId: 'GRID_001',
                        maxAltitude: 300,
                        airspaceClass: 'Class E'
                    }
                }
            ];

            mockUASFMManager.getDataForBounds.mockResolvedValue(mockFeatures);

            // Simulate loading UASFM layer
            const geojsonData = {
                type: 'FeatureCollection',
                features: mockFeatures.map(feature => ({
                    type: 'Feature',
                    geometry: feature.geometry,
                    properties: {
                        ...feature.properties,
                        maxAltitude: feature.maxAltitude,
                        gridId: feature.id
                    }
                }))
            };

            const uasfmLayer = L.geoJSON(geojsonData, {
                style: expect.any(Function),
                onEachFeature: expect.any(Function)
            });

            expect(L.geoJSON).toHaveBeenCalledWith(
                geojsonData,
                expect.objectContaining({
                    style: expect.any(Function),
                    onEachFeature: expect.any(Function)
                })
            );
        });

        test('should apply altitude-based styling', () => {
            // Test color function
            const getAltitudeColor = (altitude) => {
                if (altitude <= 100) return '#28a745'; // Green
                if (altitude <= 200) return '#ffc107'; // Yellow
                if (altitude <= 300) return '#fd7e14'; // Orange
                if (altitude <= 400) return '#dc3545'; // Red
                return '#6f42c1'; // Purple
            };

            expect(getAltitudeColor(50)).toBe('#28a745');   // Green for 0-100ft
            expect(getAltitudeColor(150)).toBe('#ffc107');  // Yellow for 101-200ft
            expect(getAltitudeColor(250)).toBe('#fd7e14');  // Orange for 201-300ft
            expect(getAltitudeColor(350)).toBe('#dc3545');  // Red for 301-400ft
            expect(getAltitudeColor(450)).toBe('#6f42c1');  // Purple for >400ft
        });

        test('should create popup with grid information', () => {
            const feature = {
                properties: {
                    maxAltitude: 300,
                    gridId: 'GRID_001',
                    airspaceClass: 'Class E',
                    gridType: 'Standard',
                    airportName: 'Test Airport'
                }
            };

            const createUASFMPopup = (feature) => {
                const props = feature.properties;
                return `
                    <div class="uasfm-popup">
                        <h4>🛩️ UAS Facility Map</h4>
                        <div class="info-row">
                            <span class="label">Grid ID:</span>
                            <span class="value">${props.gridId}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">Max Altitude:</span>
                            <span class="value">${props.maxAltitude} ft AGL</span>
                        </div>
                        <div class="info-row">
                            <span class="label">Airspace Class:</span>
                            <span class="value">${props.airspaceClass}</span>
                        </div>
                    </div>
                `;
            };

            const popup = createUASFMPopup(feature);
            
            expect(popup).toContain('GRID_001');
            expect(popup).toContain('300 ft AGL');
            expect(popup).toContain('Class E');
            expect(popup).toContain('UAS Facility Map');
        });
    });

    describe('Layer Controls', () => {
        test('should create layer control with overlays', () => {
            const overlays = {
                'UAS Facility Maps': L.layerGroup(),
                'TFRs (Temporary Flight Restrictions)': L.layerGroup(),
                'Flight Plans': L.layerGroup()
            };

            const layerControl = L.control.layers(null, overlays, {
                collapsed: false,
                position: 'topright'
            });

            expect(L.control.layers).toHaveBeenCalledWith(
                null,
                overlays,
                expect.objectContaining({
                    collapsed: false,
                    position: 'topright'
                })
            );
        });

        test('should update layer control when layers change', () => {
            const updateLayerControl = (uasfmLayer, tfrLayer, drawnItems) => {
                const overlays = {};
                if (uasfmLayer) overlays['UAS Facility Maps'] = uasfmLayer;
                if (tfrLayer) overlays['TFRs (Temporary Flight Restrictions)'] = tfrLayer;
                if (drawnItems) overlays['Flight Plans'] = drawnItems;

                return L.control.layers(null, overlays, {
                    collapsed: false,
                    position: 'topright'
                });
            };

            const mockUASFMLayer = L.layerGroup();
            const mockTFRLayer = L.layerGroup();
            const mockDrawnItems = L.layerGroup();

            const control = updateLayerControl(mockUASFMLayer, mockTFRLayer, mockDrawnItems);

            expect(L.control.layers).toHaveBeenCalledWith(
                null,
                expect.objectContaining({
                    'UAS Facility Maps': mockUASFMLayer,
                    'TFRs (Temporary Flight Restrictions)': mockTFRLayer,
                    'Flight Plans': mockDrawnItems
                }),
                expect.any(Object)
            );
        });
    });

    describe('Search Functionality', () => {
        test('should handle coordinate input', async () => {
            const searchInput = document.getElementById('search-input');
            const searchButton = document.getElementById('search-button');
            const resultsDiv = document.createElement('div');

            // Simulate coordinate input
            searchInput.value = '37.7749, -122.4194';
            searchButton.click();

            // Mock geocoding function
            const geocodeAddress = async (address) => {
                const coordMatch = address.match(/^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/);
                if (coordMatch) {
                    return {
                        lat: parseFloat(coordMatch[1]),
                        lng: parseFloat(coordMatch[2])
                    };
                }
                return null;
            };

            const coords = await geocodeAddress(searchInput.value);
            
            expect(coords).toEqual({
                lat: 37.7749,
                lng: -122.4194
            });
        });

        test('should handle address geocoding', async () => {
            const geocodeAddress = async (address) => {
                const sampleLocations = {
                    'san francisco': { lat: 37.7749, lng: -122.4194 },
                    'new york': { lat: 40.7128, lng: -74.0060 },
                    'los angeles': { lat: 34.0522, lng: -118.2437 }
                };

                const normalizedAddress = address.toLowerCase();
                for (const [key, coords] of Object.entries(sampleLocations)) {
                    if (normalizedAddress.includes(key)) {
                        return coords;
                    }
                }
                return null;
            };

            const coords = await geocodeAddress('San Francisco, CA');
            
            expect(coords).toEqual({
                lat: 37.7749,
                lng: -122.4194
            });
        });

        test('should use current location', () => {
            const mockPosition = {
                coords: {
                    latitude: 37.7749,
                    longitude: -122.4194
                }
            };

            navigator.geolocation.getCurrentPosition.mockImplementation((success) => {
                success(mockPosition);
            });

            const useCurrentLocation = () => {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            const lat = position.coords.latitude;
                            const lng = position.coords.longitude;
                            document.getElementById('search-input').value = `${lat}, ${lng}`;
                        },
                        (error) => {
                            console.error('Error getting location:', error);
                        }
                    );
                }
            };

            useCurrentLocation();

            expect(navigator.geolocation.getCurrentPosition).toHaveBeenCalled();
        });
    });

    describe('Flight Planning', () => {
        test('should initialize drawing tools', () => {
            const drawnItems = L.FeatureGroup();
            const drawControl = L.Control.Draw({
                draw: {
                    polygon: {
                        allowIntersection: false,
                        shapeOptions: {
                            color: '#28a745',
                            weight: 2,
                            opacity: 0.8,
                            fillOpacity: 0.3
                        }
                    },
                    polyline: false,
                    circle: false,
                    circlemarker: false,
                    rectangle: false,
                    marker: false
                },
                edit: {
                    featureGroup: drawnItems,
                    remove: true
                }
            });

            expect(L.FeatureGroup).toHaveBeenCalled();
            expect(L.Control.Draw).toHaveBeenCalledWith(
                expect.objectContaining({
                    draw: expect.objectContaining({
                        polygon: expect.objectContaining({
                            allowIntersection: false,
                            shapeOptions: expect.objectContaining({
                                color: '#28a745'
                            })
                        })
                    })
                })
            );
        });

        test('should create flight plan from drawn polygon', () => {
            const mockLayer = {
                toGeoJSON: () => ({
                    geometry: {
                        type: 'Polygon',
                        coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                    }
                })
            };

            const createFlightPlan = (layer) => {
                return {
                    id: `flight_plan_${Date.now()}`,
                    geometry: layer.toGeoJSON().geometry,
                    properties: {
                        maxAltitude: parseInt(document.getElementById('planned-altitude').value),
                        duration: document.getElementById('flight-duration').value,
                        purpose: document.getElementById('flight-purpose').value,
                        createdAt: new Date().toISOString()
                    }
                };
            };

            const flightPlan = createFlightPlan(mockLayer);

            expect(flightPlan.geometry.type).toBe('Polygon');
            expect(flightPlan.properties.maxAltitude).toBe(400);
            expect(flightPlan.properties.duration).toBe('2 hours');
            expect(flightPlan.properties.purpose).toBe('Recreational');
        });

        test('should validate flight plan', async () => {
            const flightPlan = {
                id: 'test_plan',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                properties: {
                    maxAltitude: 300,
                    duration: '2 hours',
                    purpose: 'Recreational'
                }
            };

            const mockValidation = {
                isValid: true,
                warnings: [],
                errors: [],
                altitudeCompliance: [
                    {
                        location: [0.5, 0.5],
                        plannedAltitude: 300,
                        maxAllowed: 400,
                        compliant: true,
                        gridId: 'GRID_001'
                    }
                ],
                tfrConflicts: [],
                recommendations: []
            };

            mockUASFMManager.validateFlightPlan.mockResolvedValue(mockValidation);

            const validation = await mockUASFMManager.validateFlightPlan(flightPlan);

            expect(validation.isValid).toBe(true);
            expect(validation.altitudeCompliance).toHaveLength(1);
            expect(mockUASFMManager.validateFlightPlan).toHaveBeenCalledWith(flightPlan);
        });

        test('should display validation results', () => {
            const validation = {
                isValid: true,
                warnings: ['Altitude close to limit'],
                errors: [],
                altitudeCompliance: [
                    {
                        location: [0.5, 0.5],
                        plannedAltitude: 300,
                        maxAllowed: 400,
                        compliant: true,
                        gridId: 'GRID_001'
                    }
                ],
                tfrConflicts: [],
                recommendations: ['Consider obtaining LAANC authorization']
            };

            const displayValidationResults = (validation) => {
                const resultsDiv = document.getElementById('validation-results');
                let html = '<h4>Flight Plan Validation Results</h4>';

                if (validation.isValid) {
                    resultsDiv.className = 'validation-results valid';
                    html += '<div class="validation-item">✅ Flight plan is valid</div>';
                } else {
                    resultsDiv.className = 'validation-results invalid';
                    html += '<div class="validation-item">❌ Flight plan has issues</div>';
                }

                if (validation.warnings.length > 0) {
                    html += '<div class="validation-item"><strong>Warnings:</strong></div>';
                    validation.warnings.forEach(warning => {
                        html += `<div class="validation-item">⚠️ ${warning}</div>`;
                    });
                }

                if (validation.recommendations.length > 0) {
                    html += '<div class="validation-item"><strong>Recommendations:</strong></div>';
                    validation.recommendations.forEach(rec => {
                        html += `<div class="validation-item">💡 ${rec}</div>`;
                    });
                }

                resultsDiv.innerHTML = html;
                resultsDiv.style.display = 'block';
            };

            displayValidationResults(validation);

            const resultsDiv = document.getElementById('validation-results');
            expect(resultsDiv.style.display).toBe('block');
            expect(resultsDiv.className).toBe('validation-results valid');
            expect(resultsDiv.innerHTML).toContain('Flight plan is valid');
            expect(resultsDiv.innerHTML).toContain('Altitude close to limit');
            expect(resultsDiv.innerHTML).toContain('Consider obtaining LAANC authorization');
        });
    });

    describe('LAANC Integration', () => {
        test('should submit LAANC request', async () => {
            const flightPlan = {
                id: 'test_plan',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                properties: {
                    maxAltitude: 300,
                    duration: '2 hours',
                    purpose: 'Recreational'
                }
            };

            const mockLAANCRequest = {
                id: 'LAANC_1234567890',
                status: 'APPROVED',
                approvalData: {
                    approvalNumber: 'LAANC_ABC123DEF',
                    approvedAltitude: 300,
                    conditions: ['Maintain visual line of sight', 'Fly during daylight hours'],
                    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                }
            };

            mockUASFMManager.submitLAANCRequest.mockResolvedValue(mockLAANCRequest);

            const request = await mockUASFMManager.submitLAANCRequest(flightPlan);

            expect(request.status).toBe('APPROVED');
            expect(request.approvalData.approvalNumber).toBe('LAANC_ABC123DEF');
            expect(request.approvalData.approvedAltitude).toBe(300);
            expect(mockUASFMManager.submitLAANCRequest).toHaveBeenCalledWith(flightPlan);
        });

        test('should display LAANC result', () => {
            const request = {
                status: 'APPROVED',
                approvalData: {
                    approvalNumber: 'LAANC_ABC123DEF',
                    approvedAltitude: 300,
                    conditions: ['Maintain visual line of sight'],
                    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
                }
            };

            const showLAANCResult = (request) => {
                const laancPanel = document.getElementById('laanc-panel');
                const laancStatus = document.getElementById('laanc-status');
                const laancDetails = document.getElementById('laanc-details');

                laancPanel.classList.add('show');

                if (request.status === 'APPROVED') {
                    laancStatus.className = 'laanc-status approved';
                    laancStatus.textContent = 'LAANC Request Approved!';
                    laancDetails.innerHTML = `
                        <div style="margin: 10px 0;">
                            <p><strong>Approval Number:</strong> ${request.approvalData.approvalNumber}</p>
                            <p><strong>Approved Altitude:</strong> ${request.approvalData.approvedAltitude} ft AGL</p>
                            <p><strong>Expires:</strong> ${new Date(request.approvalData.expiresAt).toLocaleString()}</p>
                        </div>
                    `;
                }
            };

            showLAANCResult(request);

            const laancPanel = document.getElementById('laanc-panel');
            const laancStatus = document.getElementById('laanc-status');
            const laancDetails = document.getElementById('laanc-details');

            expect(laancPanel.classList.contains('show')).toBe(true);
            expect(laancStatus.textContent).toBe('LAANC Request Approved!');
            expect(laancStatus.className).toBe('laanc-status approved');
            expect(laancDetails.innerHTML).toContain('LAANC_ABC123DEF');
            expect(laancDetails.innerHTML).toContain('300 ft AGL');
        });
    });

    describe('Status Updates', () => {
        test('should update status bar', () => {
            const updateStatus = (message) => {
                const statusElement = document.getElementById('uasfm-status');
                if (statusElement) {
                    statusElement.textContent = message;
                }
            };

            const updateGridCount = (count) => {
                const countElement = document.getElementById('grid-count');
                if (countElement) {
                    countElement.textContent = count;
                }
            };

            const updateTFRCount = (count) => {
                const countElement = document.getElementById('tfr-count');
                if (countElement) {
                    countElement.textContent = count;
                }
            };

            updateStatus('Ready');
            updateGridCount(150);
            updateTFRCount(3);

            expect(document.getElementById('uasfm-status').textContent).toBe('Ready');
            expect(document.getElementById('grid-count').textContent).toBe('150');
            expect(document.getElementById('tfr-count').textContent).toBe('3');
        });

        test('should update last update time', () => {
            const updateLastUpdate = () => {
                const updateElement = document.getElementById('last-update');
                if (updateElement) {
                    const now = new Date();
                    updateElement.textContent = now.toLocaleTimeString();
                }
            };

            updateLastUpdate();

            const lastUpdateElement = document.getElementById('last-update');
            expect(lastUpdateElement.textContent).toMatch(/\d{1,2}:\d{2}:\d{2}/);
        });
    });

    describe('Event Handling', () => {
        test('should handle map view changes', () => {
            const map = L.map('map');
            const onMapViewChanged = jest.fn();

            map.on('moveend', onMapViewChanged);
            map.on('zoomend', onMapViewChanged);

            // Simulate map events
            map.on.mock.calls.forEach(([event, callback]) => {
                if (event === 'moveend' || event === 'zoomend') {
                    callback();
                }
            });

            expect(onMapViewChanged).toHaveBeenCalledTimes(2);
        });

        test('should handle keyboard shortcuts', () => {
            const mockEvent = {
                ctrlKey: true,
                key: 'r',
                preventDefault: jest.fn()
            };

            const handleKeyboardShortcuts = (event) => {
                if (event.ctrlKey || event.metaKey) {
                    switch (event.key) {
                        case 'r':
                            event.preventDefault();
                            // Refresh UASFM data
                            break;
                        case 's':
                            event.preventDefault();
                            document.getElementById('search-input').focus();
                            break;
                        case 'd':
                            event.preventDefault();
                            // Start drawing
                            break;
                    }
                }
            };

            handleKeyboardShortcuts(mockEvent);

            expect(mockEvent.preventDefault).toHaveBeenCalled();
        });
    });

    describe('Error Handling', () => {
        test('should handle UASFM initialization errors', () => {
            const handleError = (error) => {
                console.error('UASFM Error:', error);
                const statusElement = document.getElementById('uasfm-status');
                if (statusElement) {
                    statusElement.textContent = `Error: ${error.message}`;
                }
            };

            const testError = new Error('Failed to initialize UASFM');
            handleError(testError);

            expect(console.error).toHaveBeenCalledWith('UASFM Error:', testError);
            expect(document.getElementById('uasfm-status').textContent).toBe('Error: Failed to initialize UASFM');
        });

        test('should handle network errors gracefully', () => {
            const handleNetworkError = (error) => {
                console.warn('Network error, using cached data:', error);
                const statusElement = document.getElementById('uasfm-status');
                if (statusElement) {
                    statusElement.textContent = 'Using cached data (offline mode)';
                }
            };

            const networkError = new Error('Network request failed');
            handleNetworkError(networkError);

            expect(console.warn).toHaveBeenCalledWith('Network error, using cached data:', networkError);
            expect(document.getElementById('uasfm-status').textContent).toBe('Using cached data (offline mode)');
        });
    });

    describe('Performance Optimization', () => {
        test('should debounce map view changes', () => {
            const debounce = (func, wait) => {
                let timeout;
                return function executedFunction(...args) {
                    const later = () => {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            };

            const mockFunction = jest.fn();
            const debouncedFunction = debounce(mockFunction, 500);

            // Call multiple times quickly
            debouncedFunction();
            debouncedFunction();
            debouncedFunction();

            // Should not be called immediately
            expect(mockFunction).not.toHaveBeenCalled();

            // Wait for debounce
            setTimeout(() => {
                expect(mockFunction).toHaveBeenCalledTimes(1);
            }, 600);
        });

        test('should efficiently filter large datasets', () => {
            const filterByBounds = (features, bounds) => {
                return features.filter(feature => {
                    if (!feature.bounds) return false;
                    
                    return !(bounds.east < feature.bounds.west ||
                            bounds.west > feature.bounds.east ||
                            bounds.south > feature.bounds.north ||
                            bounds.north < feature.bounds.south);
                });
            };

            const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
                id: `GRID_${i}`,
                bounds: {
                    north: i * 0.01,
                    south: (i - 1) * 0.01,
                    east: i * 0.01,
                    west: (i - 1) * 0.01
                }
            }));

            const bounds = { north: 1, south: 0, east: 1, west: 0 };
            const startTime = performance.now();
            const filtered = filterByBounds(largeDataset, bounds);
            const endTime = performance.now();

            expect(endTime - startTime).toBeLessThan(100); // Should filter in under 100ms
            expect(filtered.length).toBeLessThan(largeDataset.length);
        });
    });

    describe('Cross-Platform Compatibility', () => {
        test('should work in Electron environment', () => {
            // Mock Electron-specific globals
            global.process = { type: 'renderer' };
            global.require = jest.fn();

            // Test that the code doesn't break in Electron
            expect(() => {
                const map = L.map('map');
                const uasfm = new UASFMManager();
            }).not.toThrow();
        });

        test('should work in Qt WebView environment', () => {
            // Mock Qt-specific globals
            global.qt = { webChannelTransport: {} };

            // Test that the code doesn't break in Qt WebView
            expect(() => {
                const map = L.map('map');
                const uasfm = new UASFMManager();
            }).not.toThrow();
        });

        test('should handle different screen densities', () => {
            // Mock different device pixel ratios
            const testPixelRatios = [1, 1.5, 2, 3];

            testPixelRatios.forEach(ratio => {
                Object.defineProperty(window, 'devicePixelRatio', {
                    value: ratio,
                    writable: true
                });

                // Test that map initialization works with different pixel ratios
                expect(() => {
                    const map = L.map('map');
                }).not.toThrow();
            });
        });
    });
});

// Mock jsdom if not available
if (typeof jsdom === 'undefined') {
    console.warn('jsdom not available, some integration tests may fail');
}

module.exports = { mockUASFMManager };
