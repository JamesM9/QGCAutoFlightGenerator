# FAA UAS Facility Maps Integration Guide

This guide explains how to integrate the FAA UAS Facility Maps (UASFM) module into your existing Qt desktop application with webviews.

## Overview

The `uasfm.js` module provides a complete solution for integrating FAA UAS Facility Maps data into Leaflet-based maps. It handles:

- **Data Fetching**: Retrieves latest UASFM GeoJSON data from FAA UDDS API
- **Local Caching**: Stores data in IndexedDB for offline use
- **Automatic Updates**: Checks for updates every 56 days
- **Leaflet Integration**: Creates overlays and provides altitude information
- **Error Handling**: Robust error handling and fallback mechanisms

## Files Included

1. **`uasfm.js`** - Main UASFM integration module
2. **`map_with_uasfm_example.html`** - Complete example implementation
3. **`UASFM_INTEGRATION_GUIDE.md`** - This integration guide

## Quick Integration

### Step 1: Add the UASFM Module to Your HTML

Add the UASFM module script to your existing `map.html`:

```html
<!-- Add this after your Leaflet script -->
<script src="uasfm.js"></script>
```

### Step 2: Initialize UASFM in Your Map

Add this JavaScript code to your existing map initialization:

```javascript
// Initialize UASFM manager
let uasfmManager = null;

function initUASFM() {
    if (typeof UASFMManager !== 'undefined') {
        uasfmManager = new UASFMManager({
            apiEndpoint: 'https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson',
            updateInterval: 56 * 24 * 60 * 60 * 1000 // 56 days
        });
        
        // Set up event listeners
        uasfmManager.on('initialized', () => {
            console.log('UASFM: Ready to use');
        });
        
        uasfmManager.on('error', (error) => {
            console.error('UASFM Error:', error);
        });
    }
}

// Call this after your map is initialized
initUASFM();
```

### Step 3: Add UASFM Overlay Controls

Add a simple toggle button to your existing map controls:

```html
<!-- Add this to your map controls -->
<button onclick="toggleUASFM()" style="background: #007bff; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer;">
    🛩️ UASFM
</button>
```

```javascript
// Add this JavaScript function
let uasfmOverlay = null;

function toggleUASFM() {
    if (!uasfmManager || !uasfmManager.isInitialized) {
        alert('UASFM not ready yet, please wait...');
        return;
    }
    
    if (uasfmOverlay) {
        // Remove overlay
        uasfmOverlay.remove();
        uasfmOverlay = null;
        console.log('UASFM overlay removed');
    } else {
        // Create overlay
        uasfmOverlay = uasfmManager.createOverlay(map, {
            opacity: 0.6,
            colorByAltitude: true,
            maxAltitude: 400
        });
        map.addLayer(uasfmOverlay.layer);
        console.log('UASFM overlay added');
    }
}
```

## Advanced Integration

### Custom Overlay Options

```javascript
const uasfmOptions = {
    opacity: 0.6,                    // Overlay opacity (0-1)
    colorByAltitude: true,           // Color grid cells by altitude
    showLabels: false,               // Show altitude labels
    maxAltitude: 400,                // Maximum altitude to display
    onFeatureClick: (feature, event) => {
        // Custom click handler
        console.log('UASFM feature clicked:', feature);
    }
};

uasfmOverlay = uasfmManager.createOverlay(map, uasfmOptions);
```

### Get Altitude Information

```javascript
// Get altitude at specific location
async function getAltitudeAtLocation(lat, lng) {
    if (uasfmManager && uasfmManager.isInitialized) {
        const altitudeInfo = await uasfmManager.getAltitudeAtLocation(lat, lng);
        if (altitudeInfo) {
            console.log('Max altitude:', altitudeInfo.maxAltitude, 'ft AGL');
            console.log('Grid ID:', altitudeInfo.gridId);
            return altitudeInfo;
        }
    }
    return null;
}

// Use in map click handler
map.on('click', async function(event) {
    const altitudeInfo = await getAltitudeAtLocation(event.latlng.lat, event.latlng.lng);
    if (altitudeInfo) {
        // Display altitude information
        L.popup()
            .setLatLng(event.latlng)
            .setContent(`Max Altitude: ${altitudeInfo.maxAltitude} ft AGL`)
            .openOn(map);
    }
});
```

### Cache Management

```javascript
// Refresh UASFM data
async function refreshUASFM() {
    if (uasfmManager) {
        await uasfmManager.refresh();
        console.log('UASFM data refreshed');
    }
}

// Get cache statistics
async function getCacheStats() {
    if (uasfmManager) {
        const stats = await uasfmManager.getCacheStats();
        console.log('Cache stats:', stats);
        return stats;
    }
}

// Clear cache
async function clearCache() {
    if (uasfmManager) {
        await uasfmManager.clearCache();
        console.log('UASFM cache cleared');
    }
}
```

## Integration with Your Existing Map.html

### Minimal Integration Example

Here's how to add UASFM to your existing `map.html` with minimal changes:

```html
<!-- Add this to the <head> section after Leaflet scripts -->
<script src="uasfm.js"></script>

<!-- Add this to your existing map controls -->
<div style="position: absolute; top: 10px; right: 10px; z-index: 1000;">
    <button onclick="toggleUASFM()" style="background: #007bff; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; margin: 2px;">
        🛩️ UASFM
    </button>
</div>

<!-- Add this JavaScript after your existing map initialization -->
<script>
let uasfmManager = null;
let uasfmOverlay = null;

// Initialize UASFM
function initUASFM() {
    if (typeof UASFMManager !== 'undefined') {
        uasfmManager = new UASFMManager();
        uasfmManager.on('initialized', () => console.log('UASFM ready'));
        uasfmManager.on('error', (error) => console.error('UASFM error:', error));
    } else {
        setTimeout(initUASFM, 100);
    }
}

// Toggle UASFM overlay
function toggleUASFM() {
    if (!uasfmManager || !uasfmManager.isInitialized) {
        alert('UASFM not ready yet');
        return;
    }
    
    if (uasfmOverlay) {
        uasfmOverlay.remove();
        uasfmOverlay = null;
    } else {
        uasfmOverlay = uasfmManager.createOverlay(map, {
            opacity: 0.6,
            colorByAltitude: true,
            maxAltitude: 400
        });
        map.addLayer(uasfmOverlay.layer);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initUASFM);
</script>
```

## API Reference

### UASFMManager Class

#### Constructor Options

```javascript
const uasfmManager = new UASFMManager({
    apiEndpoint: 'https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson',
    cacheName: 'uasfm-cache',
    cacheVersion: 1,
    updateInterval: 56 * 24 * 60 * 60 * 1000, // 56 days
    maxCacheAge: 60 * 24 * 60 * 60 * 1000,    // 60 days
    gridSize: 30                              // 30 arc-seconds
});
```

#### Methods

- `createOverlay(map, options)` - Create Leaflet overlay
- `getAltitudeAtLocation(lat, lng)` - Get altitude at specific location
- `getDataForBounds(bounds, options)` - Get data for specific area
- `refresh()` - Force refresh of data
- `getCacheStats()` - Get cache statistics
- `clearCache()` - Clear all cached data
- `destroy()` - Clean up resources

#### Events

- `initialized` - Fired when UASFM is ready
- `loading` - Fired when loading data
- `loadingComplete` - Fired when loading finishes
- `dataUpdated` - Fired when data is updated
- `usingCachedData` - Fired when using cached data
- `error` - Fired when an error occurs

### Overlay Options

```javascript
const overlayOptions = {
    opacity: 0.6,                    // Overlay opacity
    colorByAltitude: true,           // Color by altitude
    showLabels: false,               // Show labels
    maxAltitude: 400,                // Max altitude to show
    onFeatureClick: (feature, event) => {
        // Custom click handler
    }
};
```

## Troubleshooting

### Common Issues

1. **"UASFM not ready" error**
   - Wait for the `initialized` event before using UASFM
   - Check that `uasfm.js` is loaded correctly

2. **No data displayed**
   - Check browser console for errors
   - Verify internet connection for initial data fetch
   - Check if cached data exists

3. **Performance issues**
   - Reduce `maxAltitude` filter
   - Use smaller map bounds
   - Clear cache if it's too large

4. **IndexedDB errors**
   - Check browser IndexedDB support
   - Clear browser data if needed
   - Use incognito mode for testing

### Debug Mode

Enable debug logging:

```javascript
const uasfmManager = new UASFMManager({
    debug: true  // Enable debug logging
});
```

## Browser Compatibility

- **Chrome**: Full support
- **Firefox**: Full support
- **Safari**: Full support
- **Edge**: Full support
- **Internet Explorer**: Not supported (no IndexedDB)

## Data Sources

The module fetches data from the official FAA UDDS API:
- **Endpoint**: `https://udds-faa.opendata.arcgis.com/datasets/UASFacilityMaps.geojson`
- **Format**: GeoJSON
- **Update Frequency**: Every 56 days
- **Coverage**: United States

## Legal and Compliance

- UASFM data is provided by the Federal Aviation Administration
- Always verify data accuracy before flight operations
- Check for NOTAMs and other restrictions
- Follow all applicable regulations and guidelines

## Support

For issues or questions:
1. Check the browser console for error messages
2. Verify the UASFM module is loaded correctly
3. Test with the provided example file
4. Check browser compatibility and IndexedDB support

## Example Files

- **`map_with_uasfm_example.html`** - Complete working example
- **`uasfm.js`** - Main UASFM module
- **`UASFM_INTEGRATION_GUIDE.md`** - This guide

The example file demonstrates all features and can be used as a reference for your integration.
