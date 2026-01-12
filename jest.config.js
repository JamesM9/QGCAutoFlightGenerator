/**
 * Jest Configuration for UASFM Tests
 * 
 * Configuration for running unit and integration tests
 */

module.exports = {
    // Test environment
    testEnvironment: 'jsdom',
    
    // Test file patterns
    testMatch: [
        '**/__tests__/**/*.js',
        '**/?(*.)+(spec|test).js'
    ],
    
    // Setup files
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    
    // Module file extensions
    moduleFileExtensions: ['js', 'json'],
    
    // Transform configuration
    transform: {
        '^.+\\.js$': 'babel-jest'
    },
    
    // Coverage configuration
    collectCoverage: true,
    coverageDirectory: 'coverage',
    coverageReporters: ['text', 'lcov', 'html'],
    coverageCollectors: [
        'text-summary',
        'lcov',
        'html'
    ],
    
    // Coverage thresholds
    coverageThreshold: {
        global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80
        }
    },
    
    // Test timeout
    testTimeout: 10000,
    
    // Verbose output
    verbose: true,
    
    // Clear mocks between tests
    clearMocks: true,
    
    // Restore mocks between tests
    restoreMocks: true,
    
    // Module name mapping
    moduleNameMapping: {
        '^@/(.*)$': '<rootDir>/src/$1'
    },
    
    // Test path ignore patterns
    testPathIgnorePatterns: [
        '/node_modules/',
        '/dist/',
        '/build/'
    ],
    
    // Collect coverage from
    collectCoverageFrom: [
        'uasfm.js',
        'map.html',
        '!**/node_modules/**',
        '!**/coverage/**',
        '!**/dist/**',
        '!**/build/**'
    ],
    
    // Global variables
    globals: {
        'ts-jest': {
            tsconfig: 'tsconfig.json'
        }
    },
    
    // Browser environment simulation
    testEnvironmentOptions: {
        url: 'http://localhost'
    },
    
    // Extensions to treat as ES modules
    extensionsToTreatAsEsm: ['.js'],
    
    // Transform ignore patterns
    transformIgnorePatterns: [
        'node_modules/(?!(leaflet|@turf)/)'
    ],
    
    // Module directories
    moduleDirectories: ['node_modules', 'src'],
    
    // Test results processor
    testResultsProcessor: 'jest-sonar-reporter',
    
    // Reporters
    reporters: [
        'default',
        ['jest-junit', {
            outputDirectory: 'reports/junit',
            outputName: 'js-test-results.xml',
            classNameTemplate: '{classname}-{title}',
            titleTemplate: '{classname}-{title}',
            ancestorSeparator: ' › ',
            usePathForSuiteName: true
        }]
    ],
    
    // Watch plugins
    watchPlugins: [
        'jest-watch-typeahead/filename',
        'jest-watch-typeahead/testname'
    ],
    
    // Notify mode
    notifyMode: 'change',
    
    // Error on deprecated
    errorOnDeprecated: true,
    
    // Force exit
    forceExit: true,
    
    // Detect open handles
    detectOpenHandles: true,
    
    // Max workers
    maxWorkers: '50%',
    
    // Worker idle memory limit
    workerIdleMemoryLimit: '512MB'
};
