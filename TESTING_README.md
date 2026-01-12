# UASFM Testing Suite

Comprehensive testing suite for the UASFM (UAS Facility Maps) integration module, including unit tests, integration tests, performance tests, and accessibility tests.

## Overview

This testing suite provides comprehensive coverage for the UASFM implementation, ensuring:

- **Unit Tests**: Core functionality testing for the UASFM module
- **Integration Tests**: Map functionality and user interactions
- **Performance Tests**: Large dataset handling and optimization
- **Accessibility Tests**: ARIA compliance and keyboard navigation
- **Cross-Platform Compatibility**: Electron and Qt WebView support

## Quick Start

### Prerequisites

- Node.js 16.0.0 or higher
- npm 8.0.0 or higher

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run all tests:**
   ```bash
   npm test
   ```

3. **Run with coverage:**
   ```bash
   npm run test:coverage
   ```

4. **Run specific test types:**
   ```bash
   # Unit tests only
   npm run test:unit
   
   # Integration tests only
   npm run test:integration
   
   # Performance tests only
   node run-tests.js --performance
   
   # Accessibility tests only
   node run-tests.js --accessibility
   ```

## Test Structure

### Unit Tests (`uasfm.test.js`)

Tests the core UASFM module functionality:

- **Constructor and Initialization**: Configuration, IndexedDB setup
- **Data Validation**: GeoJSON structure validation
- **Data Processing**: Feature processing and altitude clamping
- **Update Checking**: FAA data update detection
- **Flight Plan Validation**: TFR conflicts and altitude compliance
- **Caching**: IndexedDB operations
- **Error Handling**: Network errors and malformed data
- **Event System**: Event emission and handling
- **Utility Functions**: Geometry calculations and polygon operations
- **Performance Optimization**: Large dataset handling
- **Cross-Platform Compatibility**: Fallback mechanisms

### Integration Tests (`map.integration.test.js`)

Tests map functionality and user interactions:

- **Map Initialization**: Leaflet setup and base layers
- **UASFM Layer Management**: Overlay creation and styling
- **Layer Controls**: Toggle functionality and updates
- **Search Functionality**: Location search and geocoding
- **Flight Planning**: Drawing tools and plan creation
- **LAANC Integration**: Request submission and approval
- **Status Updates**: Real-time status display
- **Event Handling**: Map interactions and keyboard shortcuts
- **Error Handling**: Graceful error recovery
- **Performance Optimization**: Debouncing and efficient updates
- **Cross-Platform Compatibility**: Electron and Qt environments

### Performance Tests (`performance.test.js`)

Tests performance optimizations:

- **Large Dataset Processing**: 10,000+ feature handling
- **Bounds Filtering**: Efficient spatial filtering
- **Memory Management**: Memory usage optimization
- **Rendering Performance**: Smooth map updates
- **Caching Efficiency**: IndexedDB performance

### Accessibility Tests (`accessibility.test.js`)

Tests accessibility compliance:

- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard accessibility
- **Color Contrast**: WCAG compliance
- **Screen Reader Support**: Voice-over compatibility
- **Focus Management**: Proper focus handling

## Test Runner

The `run-tests.js` script provides a comprehensive test runner with the following features:

### Usage

```bash
# Run all tests
node run-tests.js

# Run specific test types
node run-tests.js --unit
node run-tests.js --integration
node run-tests.js --performance
node run-tests.js --accessibility

# Run with options
node run-tests.js --coverage --watch
node run-tests.js --ci --verbose

# Show help
node run-tests.js --help
```

### Options

- `--unit`: Run only unit tests
- `--integration`: Run only integration tests
- `--performance`: Run only performance tests
- `--accessibility`: Run only accessibility tests
- `--watch`: Run tests in watch mode
- `--coverage`: Generate coverage report
- `--verbose`: Verbose output
- `--ci`: Run in CI mode
- `--help`: Show help message

### Features

- **Automatic dependency checking**
- **Colored console output**
- **Test report generation**
- **Performance monitoring**
- **Coverage analysis**
- **CI/CD integration**

## Configuration

### Jest Configuration (`jest.config.js`)

```javascript
module.exports = {
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    collectCoverage: true,
    coverageThreshold: {
        global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80
        }
    }
};
```

### Test Setup (`jest.setup.js`)

Provides global mocks and utilities:

- **IndexedDB mocking**
- **Leaflet mocking**
- **Fetch API mocking**
- **Performance API mocking**
- **Test utilities**

## Performance Optimizations

### Large Dataset Handling

The UASFM module includes several performance optimizations:

1. **Feature Clipping**: Uses Turf.js to clip features to visible bounds
2. **Batch Processing**: Renders features in batches using `requestAnimationFrame`
3. **Debouncing**: Debounces map view changes to prevent excessive updates
4. **Color Caching**: Caches color calculations for repeated use
5. **Bounds Checking**: Skips updates when bounds haven't changed significantly

### Memory Management

- **Efficient Data Structures**: Optimized GeoJSON processing
- **Garbage Collection**: Proper cleanup of event listeners and overlays
- **Memory Monitoring**: Built-in memory usage tracking

## Accessibility Features

### ARIA Compliance

- **Proper Labels**: All interactive elements have descriptive labels
- **Role Attributes**: Correct ARIA roles for dialogs and buttons
- **Live Regions**: Dynamic content updates with `aria-live`
- **Focus Management**: Proper focus handling and keyboard navigation

### Keyboard Navigation

- **Tab Navigation**: All interactive elements are keyboard accessible
- **Enter/Space Activation**: Standard keyboard activation patterns
- **Escape Key**: Proper dialog dismissal
- **Arrow Keys**: Map navigation support

### Screen Reader Support

- **Descriptive Text**: Altitude information in natural language
- **Context Information**: Grid details and airspace class descriptions
- **Status Updates**: Real-time status announcements
- **Error Messages**: Clear error descriptions

## Cross-Platform Compatibility

### Electron Support

- **Process Detection**: Automatic Electron environment detection
- **IPC Communication**: Support for main/renderer process communication
- **File System Access**: Secure file system operations

### Qt WebView Support

- **WebChannel Integration**: Qt WebChannel transport support
- **Native Integration**: Bridge to Qt native functionality
- **Platform Detection**: Automatic Qt environment detection

### Fallback Mechanisms

- **IndexedDB Fallback**: Graceful degradation when IndexedDB unavailable
- **Fetch Fallback**: Network request fallbacks
- **Feature Detection**: Automatic feature availability detection

## Continuous Integration

### GitHub Actions

```yaml
name: UASFM Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run test:ci
      - uses: codecov/codecov-action@v3
```

### Coverage Reporting

- **Codecov Integration**: Automatic coverage reporting
- **Coverage Thresholds**: Enforced minimum coverage levels
- **Coverage Reports**: HTML and LCOV format reports

## Debugging

### Common Issues

1. **IndexedDB Errors**: Check browser compatibility and permissions
2. **Network Timeouts**: Verify FAA API endpoints and network connectivity
3. **Memory Leaks**: Monitor memory usage in long-running tests
4. **Performance Issues**: Use browser dev tools to profile rendering

### Debug Commands

```bash
# Run tests with debugging
npm run test -- --verbose --detectOpenHandles

# Run specific test with debugging
npm test -- --testNamePattern="should handle large datasets"

# Run with coverage and debugging
npm run test:coverage -- --verbose
```

## Contributing

### Adding New Tests

1. **Unit Tests**: Add to `uasfm.test.js` for module functionality
2. **Integration Tests**: Add to `map.integration.test.js` for UI interactions
3. **Performance Tests**: Add to `performance.test.js` for optimization testing
4. **Accessibility Tests**: Add to `accessibility.test.js` for compliance testing

### Test Guidelines

- **Descriptive Names**: Use clear, descriptive test names
- **Isolation**: Each test should be independent
- **Mocking**: Use appropriate mocks for external dependencies
- **Assertions**: Use specific assertions with clear error messages
- **Coverage**: Aim for high test coverage

### Code Style

- **ESLint**: Follow ESLint configuration
- **Prettier**: Use consistent code formatting
- **Comments**: Add comments for complex test logic
- **Documentation**: Update documentation for new features

## Troubleshooting

### Test Failures

1. **Check Dependencies**: Ensure all dependencies are installed
2. **Clear Cache**: Clear Jest cache with `npm test -- --clearCache`
3. **Update Mocks**: Update mocks if external APIs change
4. **Check Environment**: Verify test environment setup

### Performance Issues

1. **Monitor Memory**: Use browser dev tools to monitor memory usage
2. **Profile Rendering**: Use performance profiling tools
3. **Optimize Queries**: Review database query efficiency
4. **Batch Operations**: Ensure operations are properly batched

### Accessibility Issues

1. **Screen Reader Testing**: Test with actual screen readers
2. **Keyboard Navigation**: Verify full keyboard accessibility
3. **Color Contrast**: Use contrast checking tools
4. **ARIA Validation**: Validate ARIA attributes

## Resources

### Documentation

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Library](https://testing-library.com/docs/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Leaflet Documentation](https://leafletjs.com/reference.html)

### Tools

- [Jest](https://jestjs.io/) - Testing framework
- [jsdom](https://github.com/jsdom/jsdom) - DOM environment
- [Turf.js](https://turfjs.org/) - Geospatial analysis
- [Leaflet](https://leafletjs.com/) - Interactive maps

### Standards

- [WCAG 2.1](https://www.w3.org/TR/WCAG21/) - Web accessibility guidelines
- [ARIA](https://www.w3.org/TR/wai-aria/) - Accessible rich internet applications
- [GeoJSON](https://geojson.org/) - Geographic data format
- [FAA UASFM](https://www.faa.gov/uas/programs_partnerships/data_exchange/) - UAS Facility Maps

## License

This testing suite is part of the AutoFlightGenerator project and is licensed under the MIT License.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Contact the development team

---

**Note**: This testing suite is designed to ensure the reliability, performance, and accessibility of the UASFM integration. Regular testing is recommended to maintain code quality and user experience.
