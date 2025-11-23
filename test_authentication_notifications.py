"""
Test script for authentication notifications

This script helps verify that password reset and signup notifications
are working correctly.

Usage:
    python test_authentication_notifications.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from notification.global_service import GlobalNotificationService
from notification.notification_templates import get_template, format_notification
from auth_manager.models import Users
from django.contrib.auth.models import User


def test_password_reset_template():
    """Test password reset notification template"""
    print("\n" + "="*60)
    print("TEST 1: Password Reset Notification Template")
    print("="*60)
    
    try:
        template = get_template("password_reset_success")
        if template:
            print("✅ Template found: password_reset_success")
            print(f"   Title: {template['title']}")
            print(f"   Body: {template['body']}")
            print(f"   Deep Link: {template['deep_link']}")
            print(f"   Web Link: {template['web_link']}")
            print(f"   Priority: {template['priority']}")
            
            # Format the notification
            formatted = format_notification("password_reset_success")
            print("\n   Formatted notification:")
            print(f"   {formatted}")
            return True
        else:
            print("❌ Template not found: password_reset_success")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signup_completed_template():
    """Test signup completion notification template"""
    print("\n" + "="*60)
    print("TEST 2: Signup Completion Notification Template")
    print("="*60)
    
    try:
        template = get_template("signup_completed")
        if template:
            print("✅ Template found: signup_completed")
            print(f"   Title: {template['title']}")
            print(f"   Body: {template['body']}")
            print(f"   Deep Link: {template['deep_link']}")
            print(f"   Web Link: {template['web_link']}")
            print(f"   Priority: {template['priority']}")
            
            # Format the notification with username
            formatted = format_notification(
                "signup_completed",
                username="TestUser"
            )
            print("\n   Formatted notification:")
            print(f"   Title: {formatted['title']}")
            print(f"   Body: {formatted['body']}")
            return True
        else:
            print("❌ Template not found: signup_completed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_notification_service():
    """Test GlobalNotificationService initialization"""
    print("\n" + "="*60)
    print("TEST 3: GlobalNotificationService Initialization")
    print("="*60)
    
    try:
        service = GlobalNotificationService()
        print("✅ GlobalNotificationService initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing service: {e}")
        return False


def test_user_with_device_id():
    """Check if there are users with device_id for testing"""
    print("\n" + "="*60)
    print("TEST 4: Check Users with Device ID")
    print("="*60)
    
    try:
        # Find users with device_id
        query = """
        MATCH (user:Users)-[:PROFILE]->(profile:Profile)
        WHERE profile.device_id IS NOT NULL
        RETURN user.uid as uid, user.username as username, user.email as email, 
               profile.device_id as device_id
        LIMIT 5
        """
        
        from neomodel import db
        results, _ = db.cypher_query(query)
        
        if results:
            print(f"✅ Found {len(results)} users with device_id:")
            for row in results:
                uid, username, email, device_id = row
                print(f"   - {username or email} (UID: {uid})")
                print(f"     Device ID: {device_id[:20]}...")
            return True
        else:
            print("⚠️  No users found with device_id")
            print("   Note: Notifications require users to have device_id in their profile")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_send_password_reset_notification(test_email=None):
    """Test sending password reset notification (dry run)"""
    print("\n" + "="*60)
    print("TEST 5: Send Password Reset Notification (Dry Run)")
    print("="*60)
    
    if not test_email:
        print("⚠️  Skipping: No test email provided")
        print("   To test with real user, run:")
        print("   python test_authentication_notifications.py --email user@example.com")
        return False
    
    try:
        # Get user
        user = User.objects.filter(email=test_email).first()
        if not user:
            print(f"❌ User not found: {test_email}")
            return False
        
        # Get user node and profile
        user_node = Users.nodes.get(user_id=str(user.id))
        profile = user_node.profile.single()
        
        if not profile or not profile.device_id:
            print(f"❌ User {test_email} has no device_id")
            return False
        
        print(f"✅ User found: {test_email}")
        print(f"   UID: {user_node.uid}")
        print(f"   Device ID: {profile.device_id[:20]}...")
        
        # Send notification
        service = GlobalNotificationService()
        service.send(
            event_type="password_reset_success",
            recipients=[{
                'device_id': profile.device_id,
                'uid': user_node.uid
            }]
        )
        
        print("✅ Password reset notification sent successfully!")
        print("   Check your device for the notification")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_signup_notification(test_email=None):
    """Test sending signup completion notification (dry run)"""
    print("\n" + "="*60)
    print("TEST 6: Send Signup Completion Notification (Dry Run)")
    print("="*60)
    
    if not test_email:
        print("⚠️  Skipping: No test email provided")
        print("   To test with real user, run:")
        print("   python test_authentication_notifications.py --email user@example.com")
        return False
    
    try:
        # Get user
        user = User.objects.filter(email=test_email).first()
        if not user:
            print(f"❌ User not found: {test_email}")
            return False
        
        # Get user node and profile
        user_node = Users.nodes.get(user_id=str(user.id))
        profile = user_node.profile.single()
        
        if not profile or not profile.device_id:
            print(f"❌ User {test_email} has no device_id")
            return False
        
        print(f"✅ User found: {test_email}")
        print(f"   UID: {user_node.uid}")
        print(f"   Username: {user_node.username or 'Not set'}")
        print(f"   Device ID: {profile.device_id[:20]}...")
        
        # Send notification
        service = GlobalNotificationService()
        service.send(
            event_type="signup_completed",
            recipients=[{
                'device_id': profile.device_id,
                'uid': user_node.uid
            }],
            username=user_node.username or test_email.split('@')[0]
        )
        
        print("✅ Signup completion notification sent successfully!")
        print("   Check your device for the notification")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AUTHENTICATION NOTIFICATIONS TEST SUITE")
    print("="*60)
    
    # Parse command line arguments
    test_email = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '--email' and len(sys.argv) > 2:
            test_email = sys.argv[2]
    
    # Run tests
    results = []
    results.append(("Password Reset Template", test_password_reset_template()))
    results.append(("Signup Completion Template", test_signup_completed_template()))
    results.append(("Notification Service Init", test_notification_service()))
    results.append(("Users with Device ID", test_user_with_device_id()))
    
    if test_email:
        results.append(("Send Password Reset", test_send_password_reset_notification(test_email)))
        results.append(("Send Signup Completion", test_send_signup_notification(test_email)))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if test_email:
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Check your mobile device for notifications")
        print("2. Verify deep links work correctly")
        print("3. Check database for notification records:")
        print("   SELECT * FROM user_notification")
        print("   WHERE notification_type IN ('password_reset_success', 'signup_completed')")
        print("   ORDER BY created_at DESC LIMIT 5;")
    else:
        print("\n" + "="*60)
        print("TO TEST WITH REAL USER")
        print("="*60)
        print("Run: python test_authentication_notifications.py --email user@example.com")
        print("(Replace user@example.com with an actual user email)")
    
    print("\n")
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
