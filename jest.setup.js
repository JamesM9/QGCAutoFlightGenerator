/**
 * Jest Setup File
 * 
 * Global test setup and mocks for UASFM testing
 */

// Mock IndexedDB
const mockIndexedDB = {
    open: jest.fn(),
    deleteDatabase: jest.fn()
};

// Mock fetch
global.fetch = jest.fn();

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

// Mock performance API
global.performance = {
    now: () => Date.now()
};

// Mock console methods
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn()
};

// Mock navigator
global.navigator = {
    geolocation: {
        getCurrentPosition: jest.fn()
    },
    userAgent: 'Jest Test Environment'
};

// Mock window methods
global.window = {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    devicePixelRatio: 1
};

// Mock document methods
global.document = {
    createElement: jest.fn(() => ({
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        style: {},
        classList: {
            add: jest.fn(),
            remove: jest.fn(),
            contains: jest.fn()
        }
    })),
    getElementById: jest.fn(),
    querySelector: jest.fn(),
    querySelectorAll: jest.fn()
};

// Mock localStorage
global.localStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn()
};

// Mock sessionStorage
global.sessionStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn()
};

// Mock URL methods
global.URL = {
    createObjectURL: jest.fn(() => 'mock-url'),
    revokeObjectURL: jest.fn()
};

// Mock Blob
global.Blob = jest.fn();

// Mock FileReader
global.FileReader = jest.fn(() => ({
    readAsText: jest.fn(),
    readAsDataURL: jest.fn(),
    onload: null,
    onerror: null
}));

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 0));
global.cancelAnimationFrame = jest.fn();

// Mock setTimeout and setInterval
global.setTimeout = jest.fn((cb, delay) => {
    if (delay === 0) {
        return setTimeout(cb, 0);
    }
    return setTimeout(cb, delay);
});

global.setInterval = jest.fn((cb, delay) => {
    return setInterval(cb, delay);
});

// Mock clearTimeout and clearInterval
global.clearTimeout = jest.fn();
global.clearInterval = jest.fn();

// Mock Math.random for consistent testing
const originalMathRandom = Math.random;
Math.random = jest.fn(() => 0.5);

// Mock Date.now for consistent testing
const originalDateNow = Date.now;
Date.now = jest.fn(() => 1640995200000); // 2022-01-01 00:00:00 UTC

// Setup before each test
beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Reset global mocks
    global.indexedDB = mockIndexedDB;
    
    // Reset Math.random and Date.now
    Math.random.mockReturnValue(0.5);
    Date.now.mockReturnValue(1640995200000);
});

// Cleanup after each test
afterEach(() => {
    // Restore original functions
    Math.random = originalMathRandom;
    Date.now = originalDateNow;
});

// Global test utilities
global.testUtils = {
    // Create mock GeoJSON feature
    createMockFeature: (id, altitude, coordinates) => ({
        id: id || 'TEST_001',
        maxAltitude: altitude || 300,
        geometry: {
            type: 'Polygon',
            coordinates: coordinates || [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        properties: {
            gridId: id || 'TEST_001',
            maxAltitude: altitude || 300,
            airspaceClass: 'Class E',
            gridType: 'Standard'
        }
    }),
    
    // Create mock flight plan
    createMockFlightPlan: (altitude, coordinates) => ({
        id: 'test_plan',
        geometry: {
            type: 'Polygon',
            coordinates: coordinates || [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        properties: {
            maxAltitude: altitude || 300,
            duration: '2 hours',
            purpose: 'Recreational',
            createdAt: new Date().toISOString()
        }
    }),
    
    // Create mock TFR
    createMockTFR: (id, coordinates) => ({
        id: id || 'TFR_001',
        type: 'TFR',
        geometry: {
            type: 'Polygon',
            coordinates: coordinates || [[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]]
        },
        properties: {
            title: 'Test TFR',
            description: 'Temporary Flight Restriction for testing',
            startDate: new Date().toISOString(),
            endDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            minAltitude: 0,
            maxAltitude: 18000,
            reason: 'Testing'
        }
    }),
    
    // Mock successful fetch response
    mockSuccessfulFetch: (data) => {
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve(data),
            headers: {
                get: jest.fn((header) => {
                    if (header === 'last-modified') {
                        return 'Wed, 21 Oct 2024 07:28:00 GMT';
                    }
                    return null;
                })
            }
        });
    },
    
    // Mock failed fetch response
    mockFailedFetch: (error) => {
        global.fetch.mockRejectedValueOnce(error || new Error('Network error'));
    },
    
    // Mock IndexedDB operations
    mockIndexedDBOperation: (operation, result) => {
        const mockRequest = {
            onsuccess: null,
            onerror: null,
            result: result
        };
        
        mockIndexedDB.open.mockReturnValue(mockRequest);
        
        return mockRequest;
    }
};

// Export for use in tests
module.exports = {
    mockIndexedDB,
    testUtils: global.testUtils
};
