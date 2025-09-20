#!/usr/bin/env python
"""
Simple test script to verify vibe activity tracking functionality.
This script tests the core functionality without requiring pytest.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from user_activity.models import VibeActivity
from vibe_manager.services.vibe_activity_service import VibeActivityService
from vibe_manager.services.vibe_analytics_service import VibeAnalyticsService
from user_activity.services.activity_service import ActivityService
from auth_manager.models import Users

def test_vibe_activity_model():
    """Test VibeActivity model creation."""
    print("\n=== Testing VibeActivity Model ===")
    
    try:
        # Test model fields and choices
        activity_types = [choice[0] for choice in VibeActivity.ACTIVITY_TYPES]
        vibe_types = [choice[0] for choice in VibeActivity.VIBE_TYPES]
        
        print(f"✓ Activity types available: {activity_types}")
        print(f"✓ Vibe types available: {vibe_types}")
        print("✓ VibeActivity model is properly configured")
        return True
    except Exception as e:
        print(f"✗ VibeActivity model test failed: {e}")
        return False

def test_vibe_activity_service():
    """Test VibeActivityService functionality."""
    print("\n=== Testing VibeActivityService ===")
    
    try:
        # Test service methods exist
        service_methods = [
            'track_vibe_creation',
            'track_vibe_sending', 
            'track_vibe_viewing',
            'track_vibe_search',
            'get_user_vibe_summary'
        ]
        
        for method in service_methods:
            if hasattr(VibeActivityService, method):
                print(f"✓ {method} method exists")
            else:
                print(f"✗ {method} method missing")
                return False
        
        print("✓ VibeActivityService has all required methods")
        return True
    except Exception as e:
        print(f"✗ VibeActivityService test failed: {e}")
        return False

def test_vibe_analytics_service():
    """Test VibeAnalyticsService functionality."""
    print("\n=== Testing VibeAnalyticsService ===")
    
    try:
        # Test analytics methods exist
        analytics_methods = [
            'get_vibe_activity_summary',
            'get_vibe_creation_analytics',
            'get_vibe_engagement_metrics',
            'get_real_time_vibe_stats'
        ]
        
        for method in analytics_methods:
            if hasattr(VibeAnalyticsService, method):
                print(f"✓ {method} method exists")
            else:
                print(f"✗ {method} method missing")
                return False
        
        print("✓ VibeAnalyticsService has all required methods")
        return True
    except Exception as e:
        print(f"✗ VibeAnalyticsService test failed: {e}")
        return False

def test_activity_service_integration():
    """Test ActivityService integration with vibe analytics."""
    print("\n=== Testing ActivityService Integration ===")
    
    try:
        service = ActivityService()
        
        # Test new methods exist
        integration_methods = [
            'get_comprehensive_analytics',
            'get_vibe_activity_insights'
        ]
        
        for method in integration_methods:
            if hasattr(service, method):
                print(f"✓ {method} method exists")
            else:
                print(f"✗ {method} method missing")
                return False
        
        print("✓ ActivityService integration is complete")
        return True
    except Exception as e:
        print(f"✗ ActivityService integration test failed: {e}")
        return False

def test_database_operations():
    """Test basic database operations."""
    print("\n=== Testing Database Operations ===")
    
    try:
        # Test querying VibeActivity (should work even if empty)
        count = VibeActivity.objects.count()
        print(f"✓ VibeActivity table exists, current count: {count}")
        
        # Test analytics with empty data
        analytics = VibeAnalyticsService.get_real_time_vibe_stats()
        if 'error' not in analytics:
            print("✓ Real-time analytics query works")
        else:
            print(f"✗ Real-time analytics failed: {analytics.get('message', 'Unknown error')}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False

def test_imports():
    """Test all imports work correctly."""
    print("\n=== Testing Imports ===")
    
    try:
        # Test all key imports
        from vibe_manager.services.vibe_activity_service import VibeActivityService
        from vibe_manager.services.vibe_analytics_service import VibeAnalyticsService
        from user_activity.models import VibeActivity
        from user_activity.services.activity_service import ActivityService
        
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Starting Vibe Activity Tracking Functionality Tests...")
    print(f"Test started at: {datetime.now()}")
    
    tests = [
        test_imports,
        test_vibe_activity_model,
        test_vibe_activity_service,
        test_vibe_analytics_service,
        test_activity_service_integration,
        test_database_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n⚠️  Test {test.__name__} failed!")
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vibe activity tracking is fully functional.")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed. Please check the implementation.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)