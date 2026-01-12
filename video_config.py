#!/usr/bin/env python3
"""
Video Configuration for Tutorial System
Centralized configuration for all instructional videos
"""

# Video Configuration
VIDEO_CONFIG = {
    "aircraft_parameters": {
        "title": "Aircraft Parameters System",
        "videos": [
            {
                "title": "🎯 Aircraft Parameters Overview",
                "url": "https://youtube.com/watch?v=aircraft_params_overview",
                "description": "Complete overview of the aircraft parameters system",
                "duration": "5:30",
                "type": "youtube"
            },
            {
                "title": "📥 Importing Parameter Files",
                "url": "https://youtube.com/watch?v=import_param_files",
                "description": "Step-by-step guide to importing .param files from your aircraft",
                "duration": "4:15",
                "type": "youtube"
            },
            {
                "title": "⚙️ Creating Aircraft Configurations",
                "url": "https://youtube.com/watch?v=create_aircraft_configs",
                "description": "How to create and manage aircraft configurations",
                "duration": "6:20",
                "type": "youtube"
            },
            {
                "title": "🚁 Mission Tool Integration",
                "url": "https://youtube.com/watch?v=mission_tool_integration",
                "description": "How parameters automatically optimize flight plans",
                "duration": "7:45",
                "type": "youtube"
            },
            {
                "title": "🛠️ Troubleshooting Parameters",
                "url": "https://youtube.com/watch?v=troubleshoot_parameters",
                "description": "Common issues and solutions with parameter system",
                "duration": "8:10",
                "type": "youtube"
            }
        ]
    },
    
    "delivery_route": {
        "title": "Delivery Route Planning",
        "videos": [
            {
                "title": "🚀 Delivery Route Basics",
                "url": "https://youtube.com/watch?v=delivery_route_basics",
                "description": "Introduction to delivery route planning",
                "duration": "4:30",
                "type": "youtube"
            },
            {
                "title": "📍 Setting Coordinates",
                "url": "https://youtube.com/watch?v=setting_coordinates",
                "description": "How to set takeoff and delivery coordinates",
                "duration": "3:45",
                "type": "youtube"
            },
            {
                "title": "⚙️ Flight Parameters",
                "url": "https://youtube.com/watch?v=flight_parameters",
                "description": "Configuring altitude, speed, and waypoint settings",
                "duration": "5:20",
                "type": "youtube"
            },
            {
                "title": "📦 Delivery Methods",
                "url": "https://youtube.com/watch?v=delivery_methods",
                "description": "Payload release vs land-and-takeoff methods",
                "duration": "6:15",
                "type": "youtube"
            },
            {
                "title": "🎯 Mission Generation",
                "url": "https://youtube.com/watch?v=mission_generation",
                "description": "Generating and exporting .plan files",
                "duration": "4:50",
                "type": "youtube"
            }
        ]
    },
    
    "multi_delivery": {
        "title": "Multi-Delivery Planning",
        "videos": [
            {
                "title": "🚚 Multi-Delivery Overview",
                "url": "https://youtube.com/watch?v=multi_delivery_overview",
                "description": "Introduction to multi-point delivery missions",
                "duration": "5:15",
                "type": "youtube"
            },
            {
                "title": "📍 Multiple Delivery Points",
                "url": "https://youtube.com/watch?v=multiple_delivery_points",
                "description": "Setting up multiple delivery destinations",
                "duration": "6:30",
                "type": "youtube"
            },
            {
                "title": "🔄 Route Optimization",
                "url": "https://youtube.com/watch?v=route_optimization",
                "description": "Optimizing delivery sequence for efficiency",
                "duration": "7:20",
                "type": "youtube"
            }
        ]
    },
    
    "security_route": {
        "title": "Security Route Planning",
        "videos": [
            {
                "title": "🛡️ Security Route Basics",
                "url": "https://youtube.com/watch?v=security_route_basics",
                "description": "Introduction to security patrol missions",
                "duration": "4:45",
                "type": "youtube"
            },
            {
                "title": "🎲 Random vs Perimeter Routes",
                "url": "https://youtube.com/watch?v=random_vs_perimeter",
                "description": "Choosing between random and perimeter patrol patterns",
                "duration": "5:30",
                "type": "youtube"
            },
            {
                "title": "🗺️ Area Definition",
                "url": "https://youtube.com/watch?v=area_definition",
                "description": "Defining patrol areas with KML files",
                "duration": "6:15",
                "type": "youtube"
            }
        ]
    },
    
    "mapping_flight": {
        "title": "Mapping Flight Planning",
        "videos": [
            {
                "title": "🗺️ Mapping Flight Overview",
                "url": "https://youtube.com/watch?v=mapping_flight_overview",
                "description": "Introduction to aerial mapping missions",
                "duration": "5:00",
                "type": "youtube"
            },
            {
                "title": "📐 Camera Configuration",
                "url": "https://youtube.com/watch?v=camera_configuration",
                "description": "Setting up camera parameters for mapping",
                "duration": "7:30",
                "type": "youtube"
            },
            {
                "title": "📊 Survey Planning",
                "url": "https://youtube.com/watch?v=survey_planning",
                "description": "Planning survey grids and coverage",
                "duration": "8:15",
                "type": "youtube"
            },
            {
                "title": "📈 Overlap Calculations",
                "url": "https://youtube.com/watch?v=overlap_calculations",
                "description": "Understanding along-track and across-track overlap",
                "duration": "6:45",
                "type": "youtube"
            }
        ]
    },
    
    "structure_scan": {
        "title": "Structure Scan Planning",
        "videos": [
            {
                "title": "🏗️ Structure Scan Overview",
                "url": "https://youtube.com/watch?v=structure_scan_overview",
                "description": "Introduction to 3D structure scanning",
                "duration": "5:30",
                "type": "youtube"
            },
            {
                "title": "🔄 Orbital Patterns",
                "url": "https://youtube.com/watch?v=orbital_patterns",
                "description": "Creating orbital scan patterns around structures",
                "duration": "7:20",
                "type": "youtube"
            },
            {
                "title": "📷 Camera Angles",
                "url": "https://youtube.com/watch?v=camera_angles",
                "description": "Optimizing camera angles for 3D reconstruction",
                "duration": "6:10",
                "type": "youtube"
            }
        ]
    },
    
    "tower_inspection": {
        "title": "Tower Inspection Planning",
        "videos": [
            {
                "title": "🗼 Tower Inspection Overview",
                "url": "https://youtube.com/watch?v=tower_inspection_overview",
                "description": "Introduction to tower inspection missions",
                "duration": "4:20",
                "type": "youtube"
            },
            {
                "title": "🔄 Orbital Inspection",
                "url": "https://youtube.com/watch?v=orbital_inspection",
                "description": "Creating orbital inspection patterns",
                "duration": "5:45",
                "type": "youtube"
            }
        ]
    },
    
    "linear_flight": {
        "title": "Linear Flight Planning",
        "videos": [
            {
                "title": "📏 Linear Flight Overview",
                "url": "https://youtube.com/watch?v=linear_flight_overview",
                "description": "Introduction to linear inspection routes",
                "duration": "4:00",
                "type": "youtube"
            },
            {
                "title": "🛤️ Path Definition",
                "url": "https://youtube.com/watch?v=path_definition",
                "description": "Defining linear paths with KML files",
                "duration": "5:15",
                "type": "youtube"
            }
        ]
    },
    
    "atob_mission": {
        "title": "A-to-B Mission Planning",
        "videos": [
            {
                "title": "🎯 A-to-B Mission Overview",
                "url": "https://youtube.com/watch?v=atob_mission_overview",
                "description": "Introduction to point-to-point missions",
                "duration": "3:30",
                "type": "youtube"
            },
            {
                "title": "📍 Simple Navigation",
                "url": "https://youtube.com/watch?v=simple_navigation",
                "description": "Setting up basic navigation between two points",
                "duration": "4:15",
                "type": "youtube"
            }
        ]
    }
}

# Local video files (for embedded playback)
LOCAL_VIDEOS = {
    "demo_aircraft_params": {
        "title": "Aircraft Parameters Demo",
        "file_path": "videos/demo_aircraft_params.mp4",
        "description": "Local demonstration of aircraft parameters system"
    },
    "demo_delivery_route": {
        "title": "Delivery Route Demo",
        "file_path": "videos/demo_delivery_route.mp4",
        "description": "Local demonstration of delivery route planning"
    }
}

# Video hosting platforms
VIDEO_PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "icon": "📺",
        "base_url": "https://youtube.com/watch?v="
    },
    "vimeo": {
        "name": "Vimeo",
        "icon": "🎬",
        "base_url": "https://vimeo.com/"
    },
    "local": {
        "name": "Local File",
        "icon": "💾",
        "base_url": "file://"
    }
}

def get_videos_for_tool(tool_name):
    """Get video configuration for a specific tool"""
    return VIDEO_CONFIG.get(tool_name, {})

def get_all_video_tools():
    """Get list of all tools with video content"""
    return list(VIDEO_CONFIG.keys())

def get_video_count():
    """Get total number of videos across all tools"""
    total = 0
    for tool_config in VIDEO_CONFIG.values():
        total += len(tool_config.get("videos", []))
    return total

def get_video_by_id(tool_name, video_index):
    """Get specific video by tool name and index"""
    tool_config = VIDEO_CONFIG.get(tool_name, {})
    videos = tool_config.get("videos", [])
    if 0 <= video_index < len(videos):
        return videos[video_index]
    return None

# Example usage and testing
if __name__ == "__main__":
    print("Video Configuration System")
    print("=" * 50)
    print(f"Total tools with videos: {len(get_all_video_tools())}")
    print(f"Total videos: {get_video_count()}")
    print("\nTools with videos:")
    for tool in get_all_video_tools():
        config = get_videos_for_tool(tool)
        video_count = len(config.get("videos", []))
        print(f"  - {tool}: {video_count} videos")
    
    print("\nAircraft Parameters videos:")
    aircraft_videos = get_videos_for_tool("aircraft_parameters")
    for i, video in enumerate(aircraft_videos.get("videos", [])):
        print(f"  {i+1}. {video['title']} ({video['duration']})")
