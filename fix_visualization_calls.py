#!/usr/bin/env python3
"""
Script to update visualization calls in deliveryroute.py to use QGroundControl style
"""

# Read the delivery route file
with open('deliveryroute.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace visualizeFlightPlan calls with QGroundControl style
content = content.replace(
    'js_code = f"visualizeFlightPlan({flight_plan_json});"',
    'js_code = f"qgcVisualization.visualizeFlightPlan({flight_plan_json});"'
)

# Replace fitFlightPathBounds calls
content = content.replace(
    'fit_js = "fitFlightPathBounds();"',
    'fit_js = "qgcVisualization.fitToMission();"'
)

# Replace clearFlightPath calls  
content = content.replace(
    'js_code = "clearFlightPath();"',
    'js_code = "qgcVisualization.clearFlightPath();"'
)

# Write the updated file
with open('deliveryroute.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Updated delivery route visualization calls to QGroundControl style')
print('✅ All visualizeFlightPlan calls now use qgcVisualization.visualizeFlightPlan')
print('✅ All fitFlightPathBounds calls now use qgcVisualization.fitToMission')
print('✅ All clearFlightPath calls now use qgcVisualization.clearFlightPath')

