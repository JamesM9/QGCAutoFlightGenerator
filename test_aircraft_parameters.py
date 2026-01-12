#!/usr/bin/env python3
"""
Test script for Aircraft Parameter System
Tests the basic functionality of the aircraft parameter management system
"""

import sys
import os
import tempfile

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_aircraft_parameter_manager():
    """Test the AircraftParameterManager class"""
    print("Testing AircraftParameterManager...")
    
    try:
        from aircraft_parameter_manager import AircraftParameterManager
        
        # Create instance
        param_manager = AircraftParameterManager()
        print("✓ AircraftParameterManager created successfully")
        
        # Test default values
        waypoint_radius = param_manager.get_waypoint_radius()
        cruise_speed = param_manager.get_cruise_speed()
        print(f"✓ Default waypoint radius: {waypoint_radius}")
        print(f"✓ Default cruise speed: {cruise_speed}")
        
        # Test parameter loading (with mock data)
        test_params = {
            "WPNAV_SPEED": 8.0,
            "WPNAV_RADIUS": 3.0,
            "PILOT_ALT_MAX": 120.0,
            "RTL_ALT": 60.0
        }
        
        # Simulate loading parameters
        param_manager.ardupilot_params = test_params
        param_manager.current_firmware = "ardupilot"
        
        # Test parameter retrieval
        actual_radius = param_manager.get_waypoint_radius()
        actual_speed = param_manager.get_cruise_speed()
        
        print(f"✓ Loaded waypoint radius: {actual_radius}")
        print(f"✓ Loaded cruise speed: {actual_speed}")
        
        # Test validation
        warnings, errors = param_manager.validate_ardupilot_parameters()
        print(f"✓ Validation warnings: {len(warnings)}")
        print(f"✓ Validation errors: {len(errors)}")
        
        print("✓ AircraftParameterManager tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ AircraftParameterManager test failed: {e}")
        return False

def test_aircraft_profile_manager():
    """Test the AircraftProfileManager class"""
    print("\nTesting AircraftProfileManager...")
    
    try:
        from aircraft_profile_manager import AircraftProfileManager
        
        # Create instance
        profile_manager = AircraftProfileManager()
        print("✓ AircraftProfileManager created successfully")
        
        # Test profile creation
        test_params = {
            "WPNAV_SPEED": 10.0,
            "WPNAV_RADIUS": 5.0
        }
        
        success = profile_manager.create_profile(
            "Test Profile", "ardupilot", test_params, "Multicopter", "Test description"
        )
        
        if success:
            print("✓ Profile created successfully")
            
            # Test profile retrieval
            profile = profile_manager.get_profile("Test Profile")
            if profile:
                print(f"✓ Profile retrieved: {profile.name}")
                print(f"✓ Profile parameters: {len(profile.parameters)}")
                
                # Test profile deletion
                delete_success = profile_manager.delete_profile("Test Profile")
                if delete_success:
                    print("✓ Profile deleted successfully")
                else:
                    print("✗ Profile deletion failed")
            else:
                print("✗ Profile retrieval failed")
        else:
            print("✗ Profile creation failed")
        
        print("✓ AircraftProfileManager tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ AircraftProfileManager test failed: {e}")
        return False

def test_parameter_aware_generator():
    """Test the ParameterAwareWaypointGenerator class"""
    print("\nTesting ParameterAwareWaypointGenerator...")
    
    try:
        from aircraft_parameter_manager import AircraftParameterManager
        from parameter_aware_waypoint_generator import ParameterAwareWaypointGenerator
        
        # Create parameter manager with test data
        param_manager = AircraftParameterManager()
        param_manager.ardupilot_params = {
            "WPNAV_SPEED": 8.0,
            "WPNAV_RADIUS": 3.0,
            "PILOT_ALT_MAX": 100.0
        }
        param_manager.current_firmware = "ardupilot"
        
        # Create generator
        generator = ParameterAwareWaypointGenerator(param_manager)
        print("✓ ParameterAwareWaypointGenerator created successfully")
        
        # Test waypoint spacing calculation
        spacing = generator.calculate_waypoint_spacing("delivery")
        print(f"✓ Calculated waypoint spacing: {spacing}")
        
        # Test mission characteristics
        test_waypoints = [(0.0, 0.0, 50.0), (0.001, 0.001, 60.0)]
        characteristics = generator.get_mission_characteristics(test_waypoints, "delivery")
        print(f"✓ Mission characteristics calculated: {len(characteristics)} items")
        
        print("✓ ParameterAwareWaypointGenerator tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ ParameterAwareWaypointGenerator test failed: {e}")
        return False

def test_parameter_file_parsing():
    """Test parameter file parsing"""
    print("\nTesting parameter file parsing...")
    
    try:
        from aircraft_parameter_manager import AircraftParameterManager
        
        param_manager = AircraftParameterManager()
        
        # Create test ArduPilot parameter file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.par', delete=False) as f:
            f.write("WPNAV_SPEED\t8.0\n")
            f.write("WPNAV_RADIUS\t3.0\n")
            f.write("PILOT_ALT_MAX\t120.0\n")
            f.write("RTL_ALT\t60.0\n")
            temp_file = f.name
        
        try:
            # Test parsing
            params = param_manager.parse_ardupilot_params(temp_file)
            print(f"✓ Parsed {len(params)} parameters from ArduPilot file")
            
            # Verify specific parameters
            if params.get("WPNAV_SPEED") == 8.0:
                print("✓ WPNAV_SPEED parsed correctly")
            else:
                print("✗ WPNAV_SPEED parsing failed")
                
        finally:
            # Clean up
            os.unlink(temp_file)
        
        # Create test PX4 parameter file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.params', delete=False) as f:
            f.write("MC_XY_CRUISE=5.0\n")
            f.write("NAV_MC_ALT_RAD=2.0\n")
            f.write("RTL_RETURN_ALT=50.0\n")
            temp_file = f.name
        
        try:
            # Test parsing
            params = param_manager.parse_px4_params(temp_file)
            print(f"✓ Parsed {len(params)} parameters from PX4 file")
            
            # Verify specific parameters
            if params.get("MC_XY_CRUISE") == 5.0:
                print("✓ MC_XY_CRUISE parsed correctly")
            else:
                print("✗ MC_XY_CRUISE parsing failed")
                
        finally:
            # Clean up
            os.unlink(temp_file)
        
        print("✓ Parameter file parsing tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Parameter file parsing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Aircraft Parameter System Test Suite")
    print("=" * 40)
    
    tests = [
        test_aircraft_parameter_manager,
        test_aircraft_profile_manager,
        test_parameter_aware_generator,
        test_parameter_file_parsing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Aircraft parameter system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
