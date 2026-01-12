/**
 * Unit Tests for UASFM Module
 * 
 * Tests for FAA UAS Facility Maps integration module
 * Run with: npm test uasfm.test.js
 */

// Mock IndexedDB for testing
const mockIndexedDB = {
    open: jest.fn(),
    deleteDatabase: jest.fn()
};

// Mock fetch for testing
global.fetch = jest.fn();

// Mock console methods
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Import the UASFM module
let UASFMManager;

// Mock DOM elements
document.createElement = jest.fn(() => ({
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    style: {},
    classList: {
        add: jest.fn(),
        remove: jest.fn(),
        contains: jest.fn()
    }
}));

describe('UASFMManager', () => {
    let uasfm;
    let mockDB;
    let mockTransaction;
    let mockStore;

    beforeEach(() => {
        // Reset all mocks
        jest.clearAllMocks();
        
        // Setup mock IndexedDB
        mockStore = {
            add: jest.fn(),
            put: jest.fn(),
            get: jest.fn(),
            getAll: jest.fn(),
            count: jest.fn(),
            clear: jest.fn(),
            createIndex: jest.fn()
        };

        mockTransaction = {
            objectStore: jest.fn(() => mockStore)
        };

        mockDB = {
            createObjectStore: jest.fn(() => mockStore),
            objectStoreNames: {
                contains: jest.fn(() => false)
            },
            transaction: jest.fn(() => mockTransaction),
            close: jest.fn()
        };

        // Mock IndexedDB open
        const mockRequest = {
            onerror: null,
            onsuccess: null,
            onupgradeneeded: null,
            result: mockDB
        };

        mockIndexedDB.open.mockReturnValue(mockRequest);

        // Mock global indexedDB
        global.indexedDB = mockIndexedDB;

        // Mock Leaflet if not available
        if (typeof L === 'undefined') {
            global.L = {
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
                geoJSON: jest.fn(() => ({
                    addTo: jest.fn(),
                    remove: jest.fn()
                }))
            };
        }

        // Import the module
        UASFMManager = require('./uasfm.js');
    });

    describe('Constructor and Initialization', () => {
        test('should create instance with default configuration', () => {
            uasfm = new UASFMManager();
            
            expect(uasfm.config.apiEndpoint).toBe('https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson');
            expect(uasfm.config.cacheVersion).toBe(3);
            expect(uasfm.config.autoUpdateCheck).toBe(true);
            expect(uasfm.config.enableAuditLogging).toBe(true);
        });

        test('should create instance with custom configuration', () => {
            const customConfig = {
                apiEndpoint: 'https://custom-endpoint.com/data',
                updateInterval: 24 * 60 * 60 * 1000, // 1 day
                autoUpdateCheck: false
            };

            uasfm = new UASFMManager(customConfig);
            
            expect(uasfm.config.apiEndpoint).toBe('https://custom-endpoint.com/data');
            expect(uasfm.config.updateInterval).toBe(24 * 60 * 60 * 1000);
            expect(uasfm.config.autoUpdateCheck).toBe(false);
        });

        test('should initialize IndexedDB cache', async () => {
            // Mock successful IndexedDB open
            const mockRequest = {
                onerror: null,
                onsuccess: null,
                onupgradeneeded: null,
                result: mockDB
            };

            mockIndexedDB.open.mockReturnValue(mockRequest);

            uasfm = new UASFMManager();
            
            // Simulate successful IndexedDB open
            setTimeout(() => {
                mockRequest.onsuccess({ target: { result: mockDB } });
            }, 0);

            await new Promise(resolve => setTimeout(resolve, 10));
            
            expect(mockIndexedDB.open).toHaveBeenCalledWith('uasfm-cache', 3);
        });

        test('should handle IndexedDB initialization failure', async () => {
            const mockRequest = {
                onerror: null,
                onsuccess: null,
                onupgradeneeded: null
            };

            mockIndexedDB.open.mockReturnValue(mockRequest);

            uasfm = new UASFMManager();
            
            // Simulate IndexedDB error
            setTimeout(() => {
                mockRequest.onerror(new Error('IndexedDB failed'));
            }, 0);

            await new Promise(resolve => setTimeout(resolve, 10));
            
            expect(console.error).toHaveBeenCalled();
        });
    });

    describe('Data Validation', () => {
        test('should validate correct GeoJSON structure', () => {
            uasfm = new UASFMManager();
            
            const validGeoJSON = {
                type: 'FeatureCollection',
                features: [
                    {
                        type: 'Feature',
                        geometry: {
                            type: 'Polygon',
                            coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                        },
                        properties: {
                            maxAltitude: 400,
                            gridId: 'TEST_001'
                        }
                    }
                ]
            };

            expect(uasfm.validateGeoJSON(validGeoJSON)).toBe(true);
        });

        test('should reject invalid GeoJSON structure', () => {
            uasfm = new UASFMManager();
            
            const invalidGeoJSON = {
                type: 'FeatureCollection',
                features: [
                    {
                        type: 'Feature',
                        geometry: {
                            type: 'Polygon',
                            coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                        },
                        properties: {
                            // Missing required properties
                        }
                    }
                ]
            };

            expect(uasfm.validateGeoJSON(invalidGeoJSON)).toBe(false);
        });

        test('should reject null or undefined GeoJSON', () => {
            uasfm = new UASFMManager();
            
            expect(uasfm.validateGeoJSON(null)).toBe(false);
            expect(uasfm.validateGeoJSON(undefined)).toBe(false);
            expect(uasfm.validateGeoJSON({})).toBe(false);
        });
    });

    describe('Data Processing', () => {
        test('should process GeoJSON features correctly', () => {
            uasfm = new UASFMManager();
            
            const testFeature = {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                properties: {
                    maxAltitude: 300,
                    gridId: 'TEST_001',
                    gridType: 'standard',
                    airportName: 'Test Airport'
                }
            };

            const processed = uasfm.processFeature(testFeature);
            
            expect(processed.id).toBe('TEST_001');
            expect(processed.maxAltitude).toBe(300);
            expect(processed.gridType).toBe('standard');
            expect(processed.properties.airportName).toBe('Test Airport');
        });

        test('should clamp altitude values to 0-400 range', () => {
            uasfm = new UASFMManager();
            
            const testFeature = {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                properties: {
                    maxAltitude: 500, // Above 400
                    gridId: 'TEST_001'
                }
            };

            const processed = uasfm.processFeature(testFeature);
            expect(processed.maxAltitude).toBe(400);
        });

        test('should handle missing properties gracefully', () => {
            uasfm = new UASFMManager();
            
            const testFeature = {
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                properties: {
                    // Missing maxAltitude and gridId
                }
            };

            const processed = uasfm.processFeature(testFeature);
            
            expect(processed.maxAltitude).toBe(400); // Default value
            expect(processed.id).toBeDefined();
        });
    });

    describe('Update Checking', () => {
        test('should check for FAA updates', async () => {
            uasfm = new UASFMManager();
            
            // Mock successful HEAD request
            global.fetch.mockResolvedValueOnce({
                ok: true,
                headers: {
                    get: jest.fn((header) => {
                        if (header === 'last-modified') {
                            return 'Wed, 21 Oct 2024 07:28:00 GMT';
                        }
                        return null;
                    })
                }
            });

            await uasfm.checkForFAAUpdates();
            
            expect(global.fetch).toHaveBeenCalledWith(
                uasfm.config.metadataEndpoint,
                expect.objectContaining({
                    method: 'HEAD',
                    headers: expect.objectContaining({
                        'Accept': 'application/json'
                    })
                })
            );
        });

        test('should handle FAA update check failure', async () => {
            uasfm = new UASFMManager();
            
            // Mock failed request
            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            await uasfm.checkForFAAUpdates();
            
            expect(uasfm.isOffline).toBe(true);
            expect(console.warn).toHaveBeenCalled();
        });

        test('should detect when FAA data is newer than local', async () => {
            uasfm = new UASFMManager();
            uasfm.lastUpdate = new Date('2024-01-01').getTime(); // Old local data
            
            // Mock successful request with newer data
            global.fetch.mockResolvedValueOnce({
                ok: true,
                headers: {
                    get: jest.fn((header) => {
                        if (header === 'last-modified') {
                            return 'Wed, 21 Oct 2024 07:28:00 GMT'; // Newer than local
                        }
                        return null;
                    })
                }
            });

            await uasfm.checkForFAAUpdates();
            
            expect(uasfm.updateAvailable).toBe(true);
        });
    });

    describe('Flight Plan Validation', () => {
        test('should validate flight plan against UASFM data', async () => {
            uasfm = new UASFMManager();
            uasfm.isInitialized = true;
            
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

            // Mock altitude compliance check
            uasfm.checkAltitudeCompliance = jest.fn().mockResolvedValue([
                {
                    location: [0.5, 0.5],
                    plannedAltitude: 300,
                    maxAllowed: 400,
                    compliant: true,
                    gridId: 'TEST_001'
                }
            ]);

            const validation = await uasfm.validateFlightPlan(flightPlan);
            
            expect(validation.isValid).toBe(true);
            expect(validation.altitudeCompliance).toHaveLength(1);
        });

        test('should detect TFR conflicts', async () => {
            uasfm = new UASFMManager();
            uasfm.isInitialized = true;
            uasfm.tfrData = [
                {
                    id: 'TFR_001',
                    geometry: {
                        type: 'Polygon',
                        coordinates: [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]]
                    },
                    properties: {
                        title: 'Test TFR',
                        reason: 'Special Event'
                    }
                }
            ];

            const flightPlan = {
                id: 'test_plan',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                properties: {
                    maxAltitude: 300
                }
            };

            const validation = await uasfm.validateFlightPlan(flightPlan);
            
            expect(validation.tfrConflicts.length).toBeGreaterThan(0);
            expect(validation.isValid).toBe(false);
        });
    });

    describe('Caching', () => {
        test('should cache data in IndexedDB', async () => {
            uasfm = new UASFMManager();
            
            const testData = {
                features: [
                    {
                        id: 'TEST_001',
                        maxAltitude: 300,
                        geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] },
                        properties: { gridId: 'TEST_001' }
                    }
                ],
                timestamp: Date.now()
            };

            // Mock successful cache operations
            mockStore.add.mockImplementation((data) => ({
                onsuccess: (callback) => setTimeout(callback, 0),
                onerror: null
            }));

            await uasfm.cacheData(testData);
            
            expect(mockStore.add).toHaveBeenCalled();
        });

        test('should retrieve cached data', async () => {
            uasfm = new UASFMManager();
            
            const cachedData = [
                {
                    id: 'TEST_001',
                    maxAltitude: 300,
                    bounds: { north: 1, south: 0, east: 1, west: 0 }
                }
            ];

            mockStore.getAll.mockImplementation(() => ({
                onsuccess: (callback) => setTimeout(() => callback({ result: cachedData }), 0),
                onerror: null
            }));

            const result = await uasfm.getCachedDataForBounds({
                north: 1, south: 0, east: 1, west: 0
            });
            
            expect(result).toEqual(cachedData);
        });
    });

    describe('Error Handling', () => {
        test('should handle network errors gracefully', async () => {
            uasfm = new UASFMManager();
            
            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            await uasfm.fetchAndCacheData();
            
            expect(uasfm.isOffline).toBe(true);
            expect(console.error).toHaveBeenCalled();
        });

        test('should handle invalid API responses', async () => {
            uasfm = new UASFMManager();
            
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: 'Not Found'
            });

            await uasfm.fetchAndCacheData();
            
            expect(console.error).toHaveBeenCalledWith(
                'UASFM: Failed to fetch data:',
                expect.any(Error)
            );
        });

        test('should handle malformed GeoJSON', async () => {
            uasfm = new UASFMManager();
            
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ type: 'InvalidType' })
            });

            await uasfm.fetchAndCacheData();
            
            expect(console.error).toHaveBeenCalled();
        });
    });

    describe('Event System', () => {
        test('should emit events correctly', () => {
            uasfm = new UASFMManager();
            
            const mockCallback = jest.fn();
            uasfm.on('testEvent', mockCallback);
            
            uasfm.emit('testEvent', 'test data');
            
            expect(mockCallback).toHaveBeenCalledWith('test data');
        });

        test('should handle multiple event listeners', () => {
            uasfm = new UASFMManager();
            
            const mockCallback1 = jest.fn();
            const mockCallback2 = jest.fn();
            
            uasfm.on('testEvent', mockCallback1);
            uasfm.on('testEvent', mockCallback2);
            
            uasfm.emit('testEvent', 'test data');
            
            expect(mockCallback1).toHaveBeenCalledWith('test data');
            expect(mockCallback2).toHaveBeenCalledWith('test data');
        });

        test('should remove event listeners', () => {
            uasfm = new UASFMManager();
            
            const mockCallback = jest.fn();
            uasfm.on('testEvent', mockCallback);
            uasfm.off('testEvent', mockCallback);
            
            uasfm.emit('testEvent', 'test data');
            
            expect(mockCallback).not.toHaveBeenCalled();
        });
    });

    describe('Utility Functions', () => {
        test('should calculate bounds correctly', () => {
            uasfm = new UASFMManager();
            
            const coordinates = [
                [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
            ];
            
            const bounds = uasfm.calculateBounds(coordinates);
            
            expect(bounds.north).toBe(1);
            expect(bounds.south).toBe(0);
            expect(bounds.east).toBe(1);
            expect(bounds.west).toBe(0);
        });

        test('should detect point in polygon', () => {
            uasfm = new UASFMManager();
            
            const polygon = [[0, 0], [1, 0], [1, 1], [0, 1]];
            
            expect(uasfm.pointInPolygon([0.5, 0.5], polygon)).toBe(true);
            expect(uasfm.pointInPolygon([2, 2], polygon)).toBe(false);
        });

        test('should detect polygon intersections', () => {
            uasfm = new UASFMManager();
            
            const poly1 = {
                coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            };
            
            const poly2 = {
                coordinates: [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]]
            };
            
            expect(uasfm.polygonsIntersect(poly1, poly2)).toBe(true);
        });
    });

    describe('Performance Optimization', () => {
        test('should handle large datasets efficiently', () => {
            uasfm = new UASFMManager();
            
            // Create a large dataset
            const largeGeoJSON = {
                type: 'FeatureCollection',
                features: Array.from({ length: 1000 }, (_, i) => ({
                    type: 'Feature',
                    geometry: {
                        type: 'Polygon',
                        coordinates: [[[i, i], [i+1, i], [i+1, i+1], [i, i+1], [i, i]]]
                    },
                    properties: {
                        maxAltitude: 300,
                        gridId: `GRID_${i.toString().padStart(3, '0')}`
                    }
                }))
            };

            const startTime = performance.now();
            const processed = uasfm.processGeoJSON(largeGeoJSON);
            const endTime = performance.now();

            expect(processed.features).toHaveLength(1000);
            expect(endTime - startTime).toBeLessThan(1000); // Should process in under 1 second
        });

        test('should filter data by bounds efficiently', async () => {
            uasfm = new UASFMManager();
            uasfm.isInitialized = true;
            
            const bounds = {
                north: 1, south: 0, east: 1, west: 0
            };

            // Mock cached data
            const cachedData = Array.from({ length: 100 }, (_, i) => ({
                id: `GRID_${i}`,
                bounds: {
                    north: i * 0.01,
                    south: (i - 1) * 0.01,
                    east: i * 0.01,
                    west: (i - 1) * 0.01
                }
            }));

            mockStore.getAll.mockImplementation(() => ({
                onsuccess: (callback) => setTimeout(() => callback({ result: cachedData }), 0),
                onerror: null
            }));

            const startTime = performance.now();
            const result = await uasfm.getCachedDataForBounds(bounds);
            const endTime = performance.now();

            expect(endTime - startTime).toBeLessThan(100); // Should filter in under 100ms
        });
    });

    describe('Cross-Platform Compatibility', () => {
        test('should work without IndexedDB (fallback)', () => {
            // Mock IndexedDB not available
            const originalIndexedDB = global.indexedDB;
            global.indexedDB = undefined;

            expect(() => {
                uasfm = new UASFMManager();
            }).not.toThrow();

            global.indexedDB = originalIndexedDB;
        });

        test('should work without fetch (fallback)', () => {
            const originalFetch = global.fetch;
            global.fetch = undefined;

            expect(() => {
                uasfm = new UASFMManager();
            }).not.toThrow();

            global.fetch = originalFetch;
        });

        test('should handle different timezone formats', () => {
            uasfm = new UASFMManager();
            
            const dateStrings = [
                'Wed, 21 Oct 2024 07:28:00 GMT',
                '2024-10-21T07:28:00Z',
                '2024-10-21 07:28:00'
            ];

            dateStrings.forEach(dateString => {
                expect(() => {
                    new Date(dateString).getTime();
                }).not.toThrow();
            });
        });
    });
});

// Mock performance API if not available
if (typeof performance === 'undefined') {
    global.performance = {
        now: () => Date.now()
    };
}

// Export for testing
module.exports = { UASFMManager };
