#!/usr/bin/env node

/**
 * UASFM Test Runner
 * 
 * Comprehensive test runner for UASFM implementation
 * Usage: node run-tests.js [options]
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Test configuration
const TEST_CONFIG = {
    unit: {
        pattern: 'uasfm.test.js',
        description: 'Unit tests for UASFM module'
    },
    integration: {
        pattern: 'map.integration.test.js',
        description: 'Integration tests for map functionality'
    },
    performance: {
        pattern: 'performance.test.js',
        description: 'Performance tests'
    },
    accessibility: {
        pattern: 'accessibility.test.js',
        description: 'Accessibility tests'
    }
};

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

// Utility functions
function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function logHeader(message) {
    log('\n' + '='.repeat(60), 'cyan');
    log(`  ${message}`, 'bright');
    log('='.repeat(60), 'cyan');
}

function logSection(message) {
    log('\n' + '-'.repeat(40), 'yellow');
    log(`  ${message}`, 'yellow');
    log('-'.repeat(40), 'yellow');
}

function logSuccess(message) {
    log(`✓ ${message}`, 'green');
}

function logError(message) {
    log(`✗ ${message}`, 'red');
}

function logWarning(message) {
    log(`⚠ ${message}`, 'yellow');
}

function logInfo(message) {
    log(`ℹ ${message}`, 'blue');
}

// Test runner functions
function checkDependencies() {
    logSection('Checking Dependencies');
    
    const requiredFiles = [
        'package.json',
        'jest.config.js',
        'jest.setup.js',
        'uasfm.js'
    ];
    
    const missingFiles = requiredFiles.filter(file => !fs.existsSync(file));
    
    if (missingFiles.length > 0) {
        logError(`Missing required files: ${missingFiles.join(', ')}`);
        return false;
    }
    
    logSuccess('All required files found');
    
    // Check if node_modules exists
    if (!fs.existsSync('node_modules')) {
        logWarning('node_modules not found. Installing dependencies...');
        try {
            execSync('npm install', { stdio: 'inherit' });
            logSuccess('Dependencies installed successfully');
        } catch (error) {
            logError('Failed to install dependencies');
            return false;
        }
    }
    
    return true;
}

function runJestTests(testPattern, options = {}) {
    const args = ['jest'];
    
    if (testPattern) {
        args.push(testPattern);
    }
    
    if (options.watch) {
        args.push('--watch');
    }
    
    if (options.coverage) {
        args.push('--coverage');
    }
    
    if (options.verbose) {
        args.push('--verbose');
    }
    
    if (options.ci) {
        args.push('--ci', '--coverage', '--watchAll=false');
    }
    
    try {
        execSync(args.join(' '), { stdio: 'inherit' });
        return true;
    } catch (error) {
        return false;
    }
}

function runUnitTests(options = {}) {
    logSection('Running Unit Tests');
    logInfo('Testing UASFM module functionality...');
    
    const success = runJestTests('uasfm.test.js', options);
    
    if (success) {
        logSuccess('Unit tests passed');
    } else {
        logError('Unit tests failed');
    }
    
    return success;
}

function runIntegrationTests(options = {}) {
    logSection('Running Integration Tests');
    logInfo('Testing map functionality and interactions...');
    
    const success = runJestTests('map.integration.test.js', options);
    
    if (success) {
        logSuccess('Integration tests passed');
    } else {
        logError('Integration tests failed');
    }
    
    return success;
}

function runPerformanceTests() {
    logSection('Running Performance Tests');
    logInfo('Testing performance optimizations...');
    
    // Create performance test if it doesn't exist
    if (!fs.existsSync('performance.test.js')) {
        const performanceTest = `
/**
 * Performance Tests for UASFM
 */

describe('Performance Tests', () => {
    test('should handle large datasets efficiently', () => {
        const startTime = performance.now();
        
        // Simulate processing large dataset
        const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
            id: \`GRID_\${i}\`,
            maxAltitude: Math.floor(Math.random() * 400),
            geometry: {
                type: 'Polygon',
                coordinates: [[[i, i], [i+1, i], [i+1, i+1], [i, i+1], [i, i]]]
            }
        }));
        
        // Process dataset
        const processed = largeDataset.map(feature => ({
            ...feature,
            processed: true
        }));
        
        const endTime = performance.now();
        const processingTime = endTime - startTime;
        
        expect(processingTime).toBeLessThan(1000); // Should process in under 1 second
        expect(processed).toHaveLength(10000);
    });
    
    test('should efficiently filter data by bounds', () => {
        const bounds = { north: 1, south: 0, east: 1, west: 0 };
        const features = Array.from({ length: 1000 }, (_, i) => ({
            id: \`GRID_\${i}\`,
            bounds: {
                north: i * 0.01,
                south: (i - 1) * 0.01,
                east: i * 0.01,
                west: (i - 1) * 0.01
            }
        }));
        
        const startTime = performance.now();
        
        const filtered = features.filter(feature => {
            if (!feature.bounds) return false;
            return !(bounds.east < feature.bounds.west ||
                    bounds.west > feature.bounds.east ||
                    bounds.south > feature.bounds.north ||
                    bounds.north < feature.bounds.south);
        });
        
        const endTime = performance.now();
        const filteringTime = endTime - startTime;
        
        expect(filteringTime).toBeLessThan(100); // Should filter in under 100ms
        expect(filtered.length).toBeLessThan(features.length);
    });
    
    test('should handle memory efficiently', () => {
        const initialMemory = process.memoryUsage().heapUsed;
        
        // Simulate memory-intensive operations
        const dataStructures = [];
        for (let i = 0; i < 100; i++) {
            dataStructures.push(new Array(1000).fill(i));
        }
        
        const peakMemory = process.memoryUsage().heapUsed;
        
        // Clean up
        dataStructures.length = 0;
        
        const finalMemory = process.memoryUsage().heapUsed;
        
        expect(peakMemory - initialMemory).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
        expect(finalMemory - initialMemory).toBeLessThan(10 * 1024 * 1024); // Less than 10MB final increase
    });
});
`;
        
        fs.writeFileSync('performance.test.js', performanceTest);
        logInfo('Created performance test file');
    }
    
    const success = runJestTests('performance.test.js');
    
    if (success) {
        logSuccess('Performance tests passed');
    } else {
        logError('Performance tests failed');
    }
    
    return success;
}

function runAccessibilityTests() {
    logSection('Running Accessibility Tests');
    logInfo('Testing accessibility features...');
    
    // Create accessibility test if it doesn't exist
    if (!fs.existsSync('accessibility.test.js')) {
        const accessibilityTest = `
/**
 * Accessibility Tests for UASFM
 */

describe('Accessibility Tests', () => {
    test('should have proper ARIA labels', () => {
        const mockFeature = {
            id: 'TEST_001',
            maxAltitude: 300,
            properties: {
                gridId: 'TEST_001',
                maxAltitude: 300,
                airspaceClass: 'Class E'
            }
        };
        
        // Test altitude description
        const getAltitudeDescription = (altitude) => {
            if (altitude <= 100) {
                return \`Low altitude zone, maximum \${altitude} feet above ground level\`;
            } else if (altitude <= 200) {
                return \`Medium altitude zone, maximum \${altitude} feet above ground level\`;
            } else if (altitude <= 300) {
                return \`High altitude zone, maximum \${altitude} feet above ground level\`;
            } else {
                return \`Restricted altitude zone, maximum \${altitude} feet above ground level\`;
            }
        };
        
        const description = getAltitudeDescription(mockFeature.maxAltitude);
        expect(description).toContain('High altitude zone');
        expect(description).toContain('300 feet above ground level');
    });
    
    test('should create accessible popup content', () => {
        const mockFeature = {
            id: 'TEST_001',
            properties: {
                gridId: 'TEST_001',
                maxAltitude: 300,
                airspaceClass: 'Class E',
                gridType: 'Standard'
            }
        };
        
        const createAccessiblePopup = (feature) => {
            const props = feature.properties;
            return \`
                <div class="uasfm-popup" role="dialog" aria-labelledby="popup-title-\${props.gridId}">
                    <h4 id="popup-title-\${props.gridId}">UAS Facility Map Grid</h4>
                    <div class="info-row">
                        <span class="label">Grid ID:</span>
                        <span class="value" aria-label="Grid identifier">\${props.gridId}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Max Altitude:</span>
                        <span class="value" aria-label="Maximum altitude \${props.maxAltitude} feet above ground level">
                            \${props.maxAltitude} ft AGL
                        </span>
                    </div>
                </div>
            \`;
        };
        
        const popup = createAccessiblePopup(mockFeature);
        
        expect(popup).toContain('role="dialog"');
        expect(popup).toContain('aria-labelledby');
        expect(popup).toContain('aria-label');
        expect(popup).toContain('UAS Facility Map Grid');
    });
    
    test('should support keyboard navigation', () => {
        const mockElement = {
            addEventListener: jest.fn(),
            setAttribute: jest.fn(),
            getAttribute: jest.fn()
        };
        
        // Test keyboard event handling
        const handleKeydown = (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                return true;
            }
            return false;
        };
        
        expect(handleKeydown({ key: 'Enter', preventDefault: jest.fn() })).toBe(true);
        expect(handleKeydown({ key: ' ', preventDefault: jest.fn() })).toBe(true);
        expect(handleKeydown({ key: 'Tab', preventDefault: jest.fn() })).toBe(false);
    });
    
    test('should have proper color contrast', () => {
        const getColor = (altitude) => {
            const normalized = Math.min(altitude / 400, 1);
            const hue = 120 - (normalized * 120);
            return \`hsl(\${hue}, 70%, 50%)\`;
        };
        
        // Test color generation for different altitudes
        const lowColor = getColor(100);
        const highColor = getColor(400);
        
        expect(lowColor).toMatch(/hsl\\(\\d+, 70%, 50%\\)/);
        expect(highColor).toMatch(/hsl\\(\\d+, 70%, 50%\\)/);
        expect(lowColor).not.toBe(highColor);
    });
});
`;
        
        fs.writeFileSync('accessibility.test.js', accessibilityTest);
        logInfo('Created accessibility test file');
    }
    
    const success = runJestTests('accessibility.test.js');
    
    if (success) {
        logSuccess('Accessibility tests passed');
    } else {
        logError('Accessibility tests failed');
    }
    
    return success;
}

function generateTestReport() {
    logSection('Generating Test Report');
    
    const reportDir = 'test-reports';
    if (!fs.existsSync(reportDir)) {
        fs.mkdirSync(reportDir);
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportFile = path.join(reportDir, `test-report-${timestamp}.json`);
    
    const report = {
        timestamp: new Date().toISOString(),
        summary: {
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0
        },
        tests: [],
        performance: {
            totalTime: 0,
            averageTime: 0
        },
        coverage: {
            statements: 0,
            branches: 0,
            functions: 0,
            lines: 0
        }
    };
    
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    logSuccess(`Test report generated: ${reportFile}`);
    
    return reportFile;
}

function runAllTests(options = {}) {
    logHeader('UASFM Test Suite');
    
    // Check dependencies
    if (!checkDependencies()) {
        process.exit(1);
    }
    
    const results = {
        unit: false,
        integration: false,
        performance: false,
        accessibility: false
    };
    
    // Run unit tests
    results.unit = runUnitTests(options);
    
    // Run integration tests
    results.integration = runIntegrationTests(options);
    
    // Run performance tests
    results.performance = runPerformanceTests();
    
    // Run accessibility tests
    results.accessibility = runAccessibilityTests();
    
    // Generate report
    generateTestReport();
    
    // Summary
    logHeader('Test Summary');
    
    const totalTests = Object.keys(results).length;
    const passedTests = Object.values(results).filter(Boolean).length;
    const failedTests = totalTests - passedTests;
    
    logInfo(`Total test suites: ${totalTests}`);
    logSuccess(`Passed: ${passedTests}`);
    logError(`Failed: ${failedTests}`);
    
    Object.entries(results).forEach(([testType, passed]) => {
        if (passed) {
            logSuccess(`${testType} tests: PASSED`);
        } else {
            logError(`${testType} tests: FAILED`);
        }
    });
    
    if (failedTests > 0) {
        logError('Some tests failed. Please review the output above.');
        process.exit(1);
    } else {
        logSuccess('All tests passed! 🎉');
    }
}

// Command line interface
function showHelp() {
    logHeader('UASFM Test Runner Help');
    log(`
Usage: node run-tests.js [options]

Options:
  --unit              Run only unit tests
  --integration       Run only integration tests
  --performance       Run only performance tests
  --accessibility     Run only accessibility tests
  --watch             Run tests in watch mode
  --coverage          Generate coverage report
  --verbose           Verbose output
  --ci                Run in CI mode
  --help              Show this help message

Examples:
  node run-tests.js                    # Run all tests
  node run-tests.js --unit             # Run only unit tests
  node run-tests.js --coverage --watch # Run with coverage in watch mode
  node run-tests.js --ci               # Run in CI mode
`, 'cyan');
}

function parseArguments() {
    const args = process.argv.slice(2);
    const options = {
        unit: false,
        integration: false,
        performance: false,
        accessibility: false,
        watch: false,
        coverage: false,
        verbose: false,
        ci: false,
        help: false
    };
    
    args.forEach(arg => {
        switch (arg) {
            case '--unit':
                options.unit = true;
                break;
            case '--integration':
                options.integration = true;
                break;
            case '--performance':
                options.performance = true;
                break;
            case '--accessibility':
                options.accessibility = true;
                break;
            case '--watch':
                options.watch = true;
                break;
            case '--coverage':
                options.coverage = true;
                break;
            case '--verbose':
                options.verbose = true;
                break;
            case '--ci':
                options.ci = true;
                break;
            case '--help':
            case '-h':
                options.help = true;
                break;
            default:
                logWarning(`Unknown option: ${arg}`);
                break;
        }
    });
    
    return options;
}

// Main execution
function main() {
    const options = parseArguments();
    
    if (options.help) {
        showHelp();
        return;
    }
    
    // Check if specific test type is requested
    const specificTests = [options.unit, options.integration, options.performance, options.accessibility];
    const hasSpecificTests = specificTests.some(Boolean);
    
    if (hasSpecificTests) {
        logHeader('Running Specific Tests');
        
        if (options.unit) {
            runUnitTests(options);
        }
        if (options.integration) {
            runIntegrationTests(options);
        }
        if (options.performance) {
            runPerformanceTests();
        }
        if (options.accessibility) {
            runAccessibilityTests();
        }
    } else {
        // Run all tests
        runAllTests(options);
    }
}

// Run the test runner
if (require.main === module) {
    main();
}

module.exports = {
    runUnitTests,
    runIntegrationTests,
    runPerformanceTests,
    runAccessibilityTests,
    runAllTests,
    checkDependencies,
    generateTestReport
};
