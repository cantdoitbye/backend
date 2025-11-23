from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from neomodel import db
from notification.global_service import GlobalNotificationService
from auth_manager.models import Users
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send all scheduled notifications (run once daily)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No notifications will be sent'))
        
        self.stdout.write(self.style.SUCCESS('Starting scheduled notifications...'))
        
        total_sent = 0
        
        # 1. Pending connection requests
        sent = self.send_pending_requests_reminders(dry_run)
        total_sent += sent
        
        # 2. Profile completion reminders
        sent = self.send_profile_reminders(dry_run)
        total_sent += sent
        
        # 3. Trending topics
        sent = self.send_trending_topics(dry_run)
        total_sent += sent
        
        # 4. Community suggestions
        sent = self.send_community_suggestions(dry_run)
        total_sent += sent
        
        # 5. New users in network
        sent = self.send_new_user_notifications(dry_run)
        total_sent += sent
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Scheduled notifications complete. Total sent: {total_sent}')
        )

    def send_pending_requests_reminders(self, dry_run=False):
        """Send reminders for pending connection requests older than 24 hours"""
        self.stdout.write('\n📬 Checking for pending connection requests...')
        
        try:
            query = """
            MATCH (receiver:Users)<-[:RECEIVER]-(conn:Connection {connection_status: 'PENDING'})
            WHERE conn.created_date < datetime() - duration('P1D')
            WITH receiver, count(conn) as request_count
            WHERE request_count > 0
            RETURN receiver.uid as user_uid, request_count
            ORDER BY request_count DESC
            """
            
            results, _ = db.cypher_query(query)
            
            if not results:
                self.stdout.write('   No pending requests found.')
                return 0
            
            sent_count = 0
            service = GlobalNotificationService() if not dry_run else None
            
            for row in results:
                user_uid = row[0]
                request_count = row[1]
                
                try:
                    user = Users.nodes.get(uid=user_uid)
                    profile = user.profile.single()
                    
                    if profile and profile.device_id:
                        if dry_run:
                            self.stdout.write(f'   Would send to {user.username}: {request_count} pending requests')
                        else:
                            service.send(
                                event_type="pending_connection_requests",
                                recipients=[{
                                    'device_id': profile.device_id,
                                    'uid': user_uid
                                }],
                                request_count=request_count
                            )
                        sent_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing user {user_uid}: {e}")
            
            self.stdout.write(f'   ✓ Sent {sent_count} pending request reminders')
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in send_pending_requests_reminders: {e}")
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            return 0

    def send_profile_reminders(self, dry_run=False):
        """Send reminders to users with incomplete profiles"""
        self.stdout.write('\n👤 Checking for incomplete profiles...')
        
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            WHERE user.created_date > datetime() - duration('P7D')
            AND (profile.bio IS NULL OR profile.bio = '' OR profile.profile_image_id IS NULL)
            RETURN user.uid as user_uid, user.username as username
            LIMIT 100
            """
            
            results, _ = db.cypher_query(query)
            
            if not results:
                self.stdout.write('   No incomplete profiles found.')
                return 0
            
            sent_count = 0
            service = GlobalNotificationService() if not dry_run else None
            
            for row in results:
                user_uid = row[0]
                username = row[1]
                
                try:
                    user = Users.nodes.get(uid=user_uid)
                    profile = user.profile.single()
                    
                    if profile and profile.device_id:
                        if dry_run:
                            self.stdout.write(f'   Would send profile reminder to {username}')
                        else:
                            service.send(
                                event_type="profile_edit_reminder",
                                recipients=[{
                                    'device_id': profile.device_id,
                                    'uid': user_uid
                                }],
                                username=username
                            )
                        sent_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing user {user_uid}: {e}")
            
            self.stdout.write(f'   ✓ Sent {sent_count} profile reminders')
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in send_profile_reminders: {e}")
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            return 0

    def send_trending_topics(self, dry_run=False):
        """Send trending topic notifications matching user interests"""
        self.stdout.write('\n🔥 Checking for trending topics...')
        
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            WHERE profile.interests IS NOT NULL 
            AND profile.interests <> []
            AND profile.device_id IS NOT NULL
            RETURN user.uid as user_uid, user.username as username, profile.interests as interests, profile.device_id as device_id
            ORDER BY user.created_date DESC
            LIMIT 50
            """
            
            results, _ = db.cypher_query(query)
            
            if not results:
                self.stdout.write('   No users with interests found.')
                return 0
            
            # Mock trending topics (replace with real analytics)
            trending_topics = [
                {'name': 'AI & Machine Learning', 'keywords': ['ai', 'ml', 'machine learning', 'artificial intelligence']},
                {'name': 'Web Development', 'keywords': ['web', 'javascript', 'react', 'frontend', 'backend']},
                {'name': 'Mobile Development', 'keywords': ['mobile', 'ios', 'android', 'flutter']},
                {'name': 'Data Science', 'keywords': ['data', 'analytics', 'python', 'statistics']},
            ]
            
            sent_count = 0
            service = GlobalNotificationService() if not dry_run else None
            
            for row in results:
                user_uid = row[0]
                username = row[1]
                user_interests = row[2] or []
                device_id = row[3]
                
                # Find matching topics
                for topic in trending_topics:
                    matched = False
                    for interest in user_interests:
                        if any(keyword.lower() in interest.lower() for keyword in topic['keywords']):
                            matched = True
                            break
                    
                    if matched:
                        if dry_run:
                            self.stdout.write(f'   Would send trending topic "{topic["name"]}" to {username}')
                        else:
                            service.send(
                                event_type="trending_topic_matching_interest",
                                recipients=[{
                                    'device_id': device_id,
                                    'uid': user_uid
                                }],
                                topic_name=topic['name'],
                                username=username
                            )
                        sent_count += 1
                        break  # Only one topic per user
            
            self.stdout.write(f'   ✓ Sent {sent_count} trending topic notifications')
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in send_trending_topics: {e}")
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            return 0

    def send_community_suggestions(self, dry_run=False):
        """Send community suggestions to users"""
        self.stdout.write('\n🏘️  Checking for community suggestions...')
        
        try:
            query = """
            MATCH (user:Users)-[:PROFILE]->(profile:Profile)
            WHERE profile.interests IS NOT NULL 
            AND profile.device_id IS NOT NULL
            OPTIONAL MATCH (user)-[:MEMBER]->(membership:Membership)-[:COMMUNITY]->(community:Community)
            WITH user, profile, count(community) as community_count
            WHERE community_count < 3
            RETURN user.uid as user_uid, user.username as username, profile.interests as interests, profile.device_id as device_id
            ORDER BY user.created_date DESC
            LIMIT 50
            """
            
            results, _ = db.cypher_query(query)
            
            if not results:
                self.stdout.write('   No users needing suggestions found.')
                return 0
            
            sent_count = 0
            service = GlobalNotificationService() if not dry_run else None
            
            for row in results:
                user_uid = row[0]
                username = row[1]
                user_interests = row[2] or []
                device_id = row[3]
                
                if user_interests:
                    suggested_community = f"Communities for {user_interests[0]}"
                    
                    if dry_run:
                        self.stdout.write(f'   Would suggest communities to {username}')
                    else:
                        service.send(
                            event_type="suggested_community",
                            recipients=[{
                                'device_id': device_id,
                                'uid': user_uid
                            }],
                            username=username,
                            suggested_community=suggested_community
                        )
                    sent_count += 1
            
            self.stdout.write(f'   ✓ Sent {sent_count} community suggestions')
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in send_community_suggestions: {e}")
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            return 0

    def send_new_user_notifications(self, dry_run=False):
        """Notify users about new users with shared interests"""
        self.stdout.write('\n👋 Checking for new users...')
        
        try:
            # Find new users from last 24 hours
            query = """
            MATCH (new_user:Users)-[:PROFILE]->(new_profile:Profile)
            WHERE new_user.created_date > datetime() - duration('P1D')
            AND new_profile.interests IS NOT NULL
            AND new_profile.interests <> []
            RETURN new_user.uid as new_user_uid, new_user.username as new_username, new_profile.interests as new_interests
            LIMIT 10
            """
            
            new_users_results, _ = db.cypher_query(query)
            
            if not new_users_results:
                self.stdout.write('   No new users found.')
                return 0
            
            sent_count = 0
            service = GlobalNotificationService() if not dry_run else None
            
            for new_user_row in new_users_results:
                new_user_uid = new_user_row[0]
                new_username = new_user_row[1]
                new_interests = new_user_row[2] or []
                
                if not new_interests:
                    continue
                
                # Find users with similar interests
                similar_users_query = """
                MATCH (user:Users)-[:PROFILE]->(profile:Profile)
                WHERE user.uid <> $new_user_uid
                AND profile.device_id IS NOT NULL
                AND profile.interests IS NOT NULL
                AND any(interest IN profile.interests WHERE interest IN $new_interests)
                RETURN user.uid as user_uid, user.username as username, profile.device_id as device_id
                LIMIT 20
                """
                
                similar_results, _ = db.cypher_query(similar_users_query, {
                    'new_user_uid': new_user_uid,
                    'new_interests': new_interests
                })
                
                for similar_user_row in similar_results:
                    user_uid = similar_user_row[0]
                    username = similar_user_row[1]
                    device_id = similar_user_row[2]
                    
                    if dry_run:
                        self.stdout.write(f'   Would notify {username} about new user {new_username}')
                    else:
                        service.send(
                            event_type="new_user_in_network",
                            recipients=[{
                                'device_id': device_id,
                                'uid': user_uid
                            }],
                            new_username=new_username,
                            shared_interests=', '.join(new_interests[:2])
                        )
                    sent_count += 1
            
            self.stdout.write(f'   ✓ Sent {sent_count} new user notifications')
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in send_new_user_notifications: {e}")
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            return 0
