"""
Django management command to check what data exists for scheduled notifications
"""
from django.core.management.base import BaseCommand
from neomodel import db
from auth_manager.models import Users


class Command(BaseCommand):
    help = 'Check what data exists for scheduled notifications (debugging)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 CHECKING NOTIFICATION DATA\n'))
        
        # 1. Check total users
        self.check_total_users()
        
        # 2. Check users with profiles
        self.check_users_with_profiles()
        
        # 3. Check users with device_id
        self.check_users_with_device_id()
        
        # 4. Check incomplete profiles
        self.check_incomplete_profiles()
        
        # 5. Check pending connections
        self.check_pending_connections()
        
        # 6. Check users with interests
        self.check_users_with_interests()
        
        # 7. Check new users (last 24 hours)
        self.check_new_users()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Data check complete!\n'))

    def check_total_users(self):
        """Check total number of users"""
        self.stdout.write('\n📊 Total Users:')
        try:
            query = "MATCH (user:Users) RETURN count(user) as count"
            results, _ = db.cypher_query(query)
            count = results[0][0] if results else 0
            self.stdout.write(f'   Total users: {count}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))

    def check_users_with_profiles(self):
        """Check users with profiles"""
        self.stdout.write('\n👤 Users with Profiles:')
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            RETURN count(user) as count
            """
            results, _ = db.cypher_query(query)
            count = results[0][0] if results else 0
            self.stdout.write(f'   Users with profiles: {count}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))

    def check_users_with_device_id(self):
        """Check users with device_id (can receive notifications)"""
        self.stdout.write('\n📱 Users with Device ID:')
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            WHERE profile.device_id IS NOT NULL AND profile.device_id <> ''
            RETURN count(user) as count
            """
            results, _ = db.cypher_query(query)
            count = results[0][0] if results else 0
            self.stdout.write(f'   Users with device_id: {count}')
            
            if count > 0:
                # Show sample
                sample_query = """
                MATCH (user:Users)-[:PROFILE]->(profile:Profile)
                WHERE profile.device_id IS NOT NULL AND profile.device_id <> ''
                RETURN user.username as username, user.email as email
                LIMIT 3
                """
                sample_results, _ = db.cypher_query(sample_query)
                self.stdout.write('   Sample users:')
                for row in sample_results:
                    self.stdout.write(f'     - {row[0] or row[1]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))

    def check_incomplete_profiles(self):
        """Check users with incomplete profiles"""
        self.stdout.write('\n📝 Incomplete Profiles:')
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            WHERE user.created_date > datetime() - duration('P30D')
            AND profile.device_id IS NOT NULL
            AND (
                profile.bio IS NULL OR profile.bio = '' OR 
                profile.profile_pic_id IS NULL OR profile.profile_pic_id = '' OR
                profile.city IS NULL OR profile.city = '' OR
                profile.state IS NULL OR profile.state = ''
            )
            RETURN count(user) as count
            """
            results, _ = db.cypher_query(query)
            count = results[0][0] if results else 0
            self.stdout.write(f'   Incomplete profiles (last 30 days): {count}')
            
            if count > 0:
                # Show sample with details
                sample_query = """
                MATCH (user:Users)-[:PROFILE]->(profile:Profile)
                WHERE user.created_date > datetime() - duration('P30D')
                AND profile.device_id IS NOT NULL
                AND (
                    profile.bio IS NULL OR profile.bio = '' OR 
                    profile.profile_pic_id IS NULL OR profile.profile_pic_id = '' OR
                    profile.city IS NULL OR profile.city = '' OR
                    profile.state IS NULL OR profile.state = ''
                )
                RETURN user.username as username, user.email as email,
                       profile.bio as bio, profile.profile_pic_id as pic,
                       profile.city as city, profile.state as state
                LIMIT 3
                """
                sample_results, _ = db.cypher_query(sample_query)
                self.stdout.write('   Sample incomplete profiles:')
                for row in sample_results:
                    username = row[0] or row[1]
                    missing = []
                    if not row[2]: missing.append('bio')
                    if not row[3]: missing.append('pic')
                    if not row[4]: missing.append('city')
                    if not row[5]: missing.append('state')
                    self.stdout.write(f'     - {username} (missing: {", ".join(missing)})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))

    def check_pending_connections(self):
        """Check pending connection requests"""
        self.stdout.write('\n🔗 Pending Connections:')
        try:
            # Check Connection (old model) with "Received" status
            query_old = """
            MATCH (conn:Connection)
            WHERE conn.connection_status = 'Received'
            RETURN count(conn) as count
            """
            results_old, _ = db.cypher_query(query_old)
            count_old = results_old[0][0] if results_old else 0
            self.stdout.write(f'   Connection (Received status): {count_old}')
            
            # Check ConnectionV2 (new model) with "Pending" status
            query_v2 = """
            MATCH (conn:ConnectionV2)
            WHERE conn.connection_status = 'Pending'
            RETURN count(conn) as count
            """
            results_v2, _ = db.cypher_query(query_v2)
            count_v2 = results_v2[0][0] if results_v2 else 0
            self.stdout.write(f'   ConnectionV2 (Pending status): {count_v2}')
            
            total_pending = count_old + count_v2
            self.stdout.write(f'   Total pending connections: {total_pending}')
            
            # Check old connections older than 24 hours (both models)
            old_query = """
            MATCH (receiver:Users)-[:PROFILE]->(profile:Profile)
            WHERE profile.device_id IS NOT NULL
            OPTIONAL MATCH (receiver)<-[:HAS_RECIEVED_CONNECTION]-(conn:Connection)
            WHERE conn.connection_status = 'Received'
            AND conn.timestamp < datetime() - duration('P1D')
            OPTIONAL MATCH (receiver)-[:HAS_CONNECTION]->(conn2:ConnectionV2)
            WHERE conn2.connection_status = 'Pending'
            AND conn2.created_date < datetime() - duration('P1D')
            WITH receiver, count(conn) + count(conn2) as request_count
            WHERE request_count > 0
            RETURN count(receiver) as user_count, sum(request_count) as total_requests
            """
            old_results, _ = db.cypher_query(old_query)
            if old_results and old_results[0][0]:
                user_count = old_results[0][0]
                total_requests = old_results[0][1]
                self.stdout.write(f'   Users with old pending requests (>24h): {user_count}')
                self.stdout.write(f'   Total old pending requests: {total_requests}')
            else:
                self.stdout.write(f'   Users with old pending requests (>24h): 0')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))

    def check_users_with_interests(self):
        """Check users with interests"""
        self.stdout.write('\n🎯 Users with Interests:')
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            WHERE profile.interests IS NOT NULL 
            AND profile.interests <> []
            AND profile.device_id IS NOT NULL
            RETURN count(user) as count
            """
            results, _ = db.cypher_query(query)
            count = results[0][0] if results else 0
            self.stdout.write(f'   Users with interests: {count}')
            
            if count > 0:
                # Show sample
                sample_query = """
                MATCH (user:Users)-[:PROFILE]->(profile:Profile)
                WHERE profile.interests IS NOT NULL 
                AND profile.interests <> []
                AND profile.device_id IS NOT NULL
                RETURN user.username as username, profile.interests as interests
                LIMIT 3
                """
                sample_results, _ = db.cypher_query(sample_query)
                self.stdout.write('   Sample users with interests:')
                for row in sample_results:
                    interests = row[1][:3] if row[1] else []
                    self.stdout.write(f'     - {row[0]}: {", ".join(interests)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))

    def check_new_users(self):
        """Check new users (last 24 hours)"""
        self.stdout.write('\n🆕 New Users (Last 24 Hours):')
        try:
            query = """
            MATCH (user:Users)
            WHERE user.created_date > datetime() - duration('P1D')
            RETURN count(user) as count
            """
            results, _ = db.cypher_query(query)
            count = results[0][0] if results else 0
            self.stdout.write(f'   New users (last 24h): {count}')
            
            # Check last 7 days
            week_query = """
            MATCH (user:Users)
            WHERE user.created_date > datetime() - duration('P7D')
            RETURN count(user) as count
            """
            week_results, _ = db.cypher_query(week_query)
            week_count = week_results[0][0] if week_results else 0
            self.stdout.write(f'   New users (last 7 days): {week_count}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))
