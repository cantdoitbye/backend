#!/usr/bin/env python3
"""
WebSocket Test Script
Run this to get a JWT token and test WebSocket connection
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/code')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from auth_manager.models import User
from graphql_jwt.shortcuts import get_token

def main():
    print("=" * 60)
    print("WebSocket Authentication Token Generator")
    print("=" * 60)
    
    # Get first user
    try:
        user = User.nodes.first()
        if not user:
            print("\n❌ No users found in database!")
            print("Please create a user first.")
            return
        
        print(f"\n✅ Found user: {user.username}")
        print(f"   UID: {user.uid}")
        
        # Generate token
        token = get_token(user)
        
        print(f"\n🔑 JWT Token:")
        print("-" * 60)
        print(token)
        print("-" * 60)
        
        print(f"\n📡 Test WebSocket Connection:")
        print(f'wscat -c "ws://localhost:8000/ws/events/" -H "Authorization: Bearer {token}"')
        
        print(f"\n🌐 Or use in browser console:")
        print(f"""
const ws = new WebSocket('ws://localhost:8000/ws/events/');
ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('📨', JSON.parse(e.data));
ws.send(JSON.stringify({{
    event_type: 'profile_view',
    data: {{ target_uid: 'test_user_123' }}
}}));
""")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
