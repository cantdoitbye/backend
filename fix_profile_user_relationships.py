"""
Script to Diagnose and Fix Missing Profile-User Relationships
=============================================================

This script identifies profiles without proper HAS_USER relationships
and automatically creates them based on the user_id field.

Issue: myProfile query returns user: null
Root Cause: Profile nodes don't have HAS_USER relationships to Users nodes

Usage:
    python fix_profile_user_relationships.py [--dry-run] [--fix]
    
Options:
    --dry-run: Only show what would be fixed without making changes
    --fix: Actually create the missing relationships
"""

import os
import sys
import django
import argparse
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialooumph.settings')
django.setup()

from auth_manager.models import Profile, Users
from neomodel import db


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print('=' * 80)


def check_profile_user_relationships():
    """
    Check for profiles without HAS_USER relationships.
    Returns list of (profile, expected_user) tuples
    """
    print_section("Checking Profile-User Relationships")
    
    # Query to find profiles without HAS_USER relationships
    query = """
    MATCH (p:Profile)
    WHERE NOT (p)-[:HAS_USER]->(:Users)
    RETURN p.uid as profile_uid, p.user_id as user_id
    """
    
    results, _ = db.cypher_query(query)
    
    missing_relationships = []
    
    if not results:
        print("✅ All profiles have proper HAS_USER relationships!")
        return missing_relationships
    
    print(f"Found {len(results)} profiles without HAS_USER relationships:")
    print()
    
    for result in results:
        profile_uid = result[0]
        user_id = result[1]
        
        try:
            # Get the profile and user nodes
            profile = Profile.nodes.get(uid=profile_uid)
            user = Users.nodes.get(user_id=user_id)
            
            missing_relationships.append((profile, user))
            
            print(f"  ❌ Profile UID: {profile_uid}")
            print(f"     User ID: {user_id}")
            print(f"     User UID: {user.uid}")
            print(f"     Username: {user.username}")
            print()
            
        except Profile.DoesNotExist:
            print(f"  ⚠️  Profile {profile_uid} not found")
        except Users.DoesNotExist:
            print(f"  ⚠️  User with user_id {user_id} not found")
    
    return missing_relationships


def fix_relationships(missing_relationships, dry_run=True):
    """
    Create HAS_USER relationships for profiles.
    
    Args:
        missing_relationships: List of (profile, user) tuples
        dry_run: If True, only simulate the fix without making changes
    """
    if not missing_relationships:
        return
    
    print_section(f"{'[DRY RUN] ' if dry_run else ''}Fixing Relationships")
    
    success_count = 0
    error_count = 0
    
    for profile, user in missing_relationships:
        try:
            if dry_run:
                print(f"  🔧 Would create: Profile({profile.uid}) -[HAS_USER]-> Users({user.uid})")
            else:
                # Create the HAS_USER relationship
                profile.user.connect(user)
                print(f"  ✅ Created: Profile({profile.uid}) -[HAS_USER]-> Users({user.uid})")
                success_count += 1
                
        except Exception as e:
            print(f"  ❌ Error fixing Profile({profile.uid}): {str(e)}")
            error_count += 1
    
    print()
    if not dry_run:
        print(f"Summary: {success_count} fixed, {error_count} errors")


def verify_fix():
    """
    Verify that all profiles now have HAS_USER relationships.
    """
    print_section("Verification")
    
    query = """
    MATCH (p:Profile)
    WHERE NOT (p)-[:HAS_USER]->(:Users)
    RETURN count(p) as missing_count
    """
    
    results, _ = db.cypher_query(query)
    missing_count = results[0][0]
    
    if missing_count == 0:
        print("✅ SUCCESS: All profiles now have HAS_USER relationships!")
        return True
    else:
        print(f"⚠️  WARNING: Still {missing_count} profiles without HAS_USER relationships")
        return False


def test_my_profile_query(user_id):
    """
    Test the myProfile query for a specific user.
    
    Args:
        user_id: The user_id to test
    """
    print_section(f"Testing myProfile Query for user_id: {user_id}")
    
    try:
        profile = Profile.nodes.get(user_id=user_id)
        print(f"✅ Profile found: {profile.uid}")
        
        # Check if HAS_USER relationship exists
        query = """
        MATCH (p:Profile {uid: $profile_uid})
        OPTIONAL MATCH (p)-[:HAS_USER]->(u:Users)
        RETURN u
        """
        
        results, _ = db.cypher_query(query, {'profile_uid': profile.uid})
        user_node = results[0][0] if results and results[0][0] else None
        
        if user_node:
            print(f"✅ HAS_USER relationship exists")
            print(f"   User: {user_node.get('username')} ({user_node.get('uid')})")
        else:
            print(f"❌ HAS_USER relationship missing!")
            
    except Profile.DoesNotExist:
        print(f"❌ Profile not found for user_id: {user_id}")


def main():
    parser = argparse.ArgumentParser(description='Fix missing Profile-User relationships')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    parser.add_argument('--fix', action='store_true', help='Actually fix the relationships')
    parser.add_argument('--test-user', type=str, help='Test myProfile query for specific user_id')
    
    args = parser.parse_args()
    
    if args.test_user:
        test_my_profile_query(args.test_user)
        return
    
    print_section("Profile-User Relationship Diagnostic Tool")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not args.dry_run and not args.fix:
        print("⚠️  No action specified. Use --dry-run to simulate or --fix to apply changes.")
        print()
        parser.print_help()
        return
    
    # Check for missing relationships
    missing_relationships = check_profile_user_relationships()
    
    if not missing_relationships:
        print("\n✅ No fixes needed!")
        return
    
    # Fix relationships
    if args.fix:
        confirm = input(f"\n⚠️  About to create {len(missing_relationships)} relationships. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    
    fix_relationships(missing_relationships, dry_run=args.dry_run)
    
    # Verify if fix was applied
    if args.fix:
        verify_fix()
    
    print()
    print("=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

