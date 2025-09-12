"""
Management command to seed the database with sample data for testing.
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from feed_algorithm.models import (
    UserProfile, Connection, Interest, InterestCollection, FeedComposition
)
from feed_content_types.models import Post, Community, Product


class Command(BaseCommand):
    help = 'Seed the database with sample data for testing the feed algorithm'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=200,
            help='Number of posts to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()
        
        self.stdout.write('Creating sample data...')
        
        # Create interests
        interests = self.create_interests()
        self.stdout.write(f'Created {len(interests)} interests')
        
        # Create users
        users = self.create_users(options['users'])
        self.stdout.write(f'Created {len(users)} users')
        
        # Create user profiles and interests
        self.create_user_profiles(users, interests)
        self.stdout.write('Created user profiles and interest collections')
        
        # Create connections
        connections = self.create_connections(users)
        self.stdout.write(f'Created {len(connections)} connections')
        
        # Create communities
        communities = self.create_communities(users)
        self.stdout.write(f'Created {len(communities)} communities')
        
        # Create posts
        posts = self.create_posts(users, options['posts'], interests)
        self.stdout.write(f'Created {len(posts)} posts')
        
        # Create products
        products = self.create_products(users)
        self.stdout.write(f'Created {len(products)} products')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database!')
        )
    
    def clear_data(self):
        """Clear existing test data."""
        User.objects.filter(username__startswith='testuser').delete()
        Interest.objects.filter(name__startswith='Test').delete()
    
    def create_interests(self):
        """Create sample interests."""
        interest_data = [
            ('Technology', 'tech'), ('Artificial Intelligence', 'tech'),
            ('Machine Learning', 'tech'), ('Web Development', 'tech'),
            ('Mobile Apps', 'tech'), ('Gaming', 'entertainment'),
            ('Movies', 'entertainment'), ('Music', 'entertainment'),
            ('Sports', 'sports'), ('Football', 'sports'),
            ('Basketball', 'sports'), ('Fitness', 'health'),
            ('Nutrition', 'health'), ('Travel', 'lifestyle'),
            ('Photography', 'lifestyle'), ('Cooking', 'lifestyle'),
            ('Business', 'business'), ('Entrepreneurship', 'business'),
            ('Marketing', 'business'), ('Education', 'education')
        ]
        
        interests = []
        for name, category in interest_data:
            interest, created = Interest.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': f'Interest in {name.lower()}',
                    'popularity_score': random.uniform(0.1, 1.0),
                    'is_trending': random.choice([True, False])
                }
            )
            interests.append(interest)
        
        return interests
    
    def create_users(self, count):
        """Create sample users."""
        users = []
        
        for i in range(1, count + 1):
            username = f'testuser{i:03d}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'Test{i}',
                    'last_name': 'User',
                    'is_active': True
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            users.append(user)
        
        return users
    
    def create_user_profiles(self, users, interests):
        """Create user profiles and assign interests."""
        languages = ['en', 'es', 'fr', 'de']
        privacy_levels = ['public', 'friends', 'private']
        
        for user in users:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'feed_enabled': True,
                    'content_language': random.choice(languages),
                    'privacy_level': random.choice(privacy_levels),
                    'total_engagement_score': random.uniform(0, 1000)
                }
            )
            
            # Create feed composition
            total = 1.0
            personal = random.uniform(0.3, 0.5)
            interest = random.uniform(0.2, 0.3)
            trending = random.uniform(0.1, 0.2)
            discovery = random.uniform(0.05, 0.15)
            community = random.uniform(0.02, 0.08)
            product = max(0.01, total - (personal + interest + trending + discovery + community))
            
            FeedComposition.objects.get_or_create(
                user=user,
                defaults={
                    'personal_connections': personal,
                    'interest_based': interest,
                    'trending_content': trending,
                    'discovery_content': discovery,
                    'community_content': community,
                    'product_content': product
                }
            )
            
            # Assign random interests
            user_interests = random.sample(interests, random.randint(3, 8))
            for interest in user_interests:
                InterestCollection.objects.get_or_create(
                    user=user,
                    interest=interest,
                    defaults={
                        'strength': random.uniform(0.1, 1.0),
                        'source': random.choice(['explicit', 'inferred', 'behavioral'])
                    }
                )
    
    def create_connections(self, users):
        """Create connections between users."""
        connections = []
        circle_types = ['inner', 'outer', 'universe']
        
        for user in users:
            # Each user follows 5-15 other users
            num_connections = random.randint(5, 15)
            connected_users = random.sample(
                [u for u in users if u != user], 
                min(num_connections, len(users) - 1)
            )
            
            for connected_user in connected_users:
                connection, created = Connection.objects.get_or_create(
                    from_user=user,
                    to_user=connected_user,
                    defaults={
                        'circle_type': random.choice(circle_types),
                        'interaction_count': random.randint(0, 50),
                        'last_interaction': timezone.now() - timedelta(
                            days=random.randint(0, 30)
                        )
                    }
                )
                if created:
                    connections.append(connection)
        
        return connections
    
    def create_communities(self, users):
        """Create sample communities."""
        community_data = [
            ('Tech Innovators', 'technology', 'A community for tech enthusiasts'),
            ('Movie Buffs', 'entertainment', 'Discuss the latest movies and shows'),
            ('Fitness Warriors', 'health', 'Share fitness tips and motivation'),
            ('Travel Explorers', 'lifestyle', 'Share travel experiences and tips'),
            ('Startup Founders', 'business', 'Connect with fellow entrepreneurs'),
            ('Photography Club', 'lifestyle', 'Share and learn photography techniques'),
            ('Gaming Guild', 'entertainment', 'Connect with fellow gamers'),
            ('Healthy Eating', 'health', 'Share healthy recipes and nutrition tips')
        ]
        
        communities = []
        for title, category, description in community_data:
            creator = random.choice(users)
            community, created = Community.objects.get_or_create(
                title=title,
                defaults={
                    'description': description,
                    'creator': creator,
                    'category': category,
                    'is_private': random.choice([True, False]),
                    'requires_approval': random.choice([True, False]),
                    'member_count': random.randint(10, 1000),
                    'engagement_score': random.uniform(10, 500)
                }
            )
            if created:
                communities.append(community)
        
        return communities
    
    def create_posts(self, users, count, interests):
        """Create sample posts."""
        post_templates = [
            "Just discovered an amazing new {topic}! Has anyone else tried this?",
            "Thoughts on the latest developments in {topic}? I'm really excited about the possibilities.",
            "Looking for recommendations on {topic}. What are your favorites?",
            "Had an incredible experience with {topic} today. Here's what I learned...",
            "Quick tip about {topic}: This simple trick changed everything for me.",
            "Can't believe how much {topic} has evolved over the years. What's next?",
            "Just finished a deep dive into {topic}. Here are my key takeaways.",
            "Weekend project involving {topic} turned out better than expected!"
        ]
        
        posts = []
        for i in range(count):
            creator = random.choice(users)
            topic = random.choice(interests).name.lower()
            
            title = f"Post about {topic} #{i+1}"
            content = random.choice(post_templates).format(topic=topic)
            
            # Add more content for some posts
            if random.random() > 0.5:
                content += f" I've been exploring this for a while now and found some interesting insights. The key is to approach {topic} with an open mind and willingness to experiment. What are your thoughts?"
            
            post = Post.objects.create(
                title=title,
                content=content,
                creator=creator,
                post_type=random.choice(['text', 'image', 'video', 'link']),
                visibility=random.choice(['public', 'friends', 'private']),
                view_count=random.randint(0, 1000),
                like_count=random.randint(0, 100),
                share_count=random.randint(0, 20),
                comment_count=random.randint(0, 50),
                engagement_score=random.uniform(1, 100),
                quality_score=random.uniform(0.1, 1.0),
                trending_score=random.uniform(0, 50),
                tags=[topic, random.choice(interests).name.lower()],
                published_at=timezone.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23)
                )
            )
            posts.append(post)
        
        return posts
    
    def create_products(self, users):
        """Create sample products."""
        product_data = [
            ('Wireless Headphones', 'electronics', 99.99, 'High-quality wireless headphones'),
            ('Fitness Tracker', 'electronics', 149.99, 'Track your fitness goals'),
            ('Coffee Maker', 'home', 79.99, 'Perfect morning coffee every time'),
            ('Running Shoes', 'sports', 129.99, 'Comfortable running shoes'),
            ('Laptop Stand', 'electronics', 49.99, 'Ergonomic laptop stand'),
            ('Water Bottle', 'sports', 24.99, 'Insulated water bottle'),
            ('Phone Case', 'electronics', 19.99, 'Protective phone case'),
            ('Yoga Mat', 'sports', 39.99, 'Non-slip yoga mat')
        ]
        
        products = []
        for title, category, price, description in product_data:
            creator = random.choice(users)
            
            product = Product.objects.create(
                title=title,
                description=description,
                creator=creator,
                price=price,
                currency='USD',
                category=category,
                brand=f'Brand{random.randint(1, 10)}',
                stock_quantity=random.randint(0, 100),
                is_in_stock=True,
                view_count=random.randint(0, 500),
                like_count=random.randint(0, 50),
                share_count=random.randint(0, 10),
                comment_count=random.randint(0, 20),
                engagement_score=random.uniform(1, 50),
                quality_score=random.uniform(0.1, 1.0),
                published_at=timezone.now() - timedelta(
                    days=random.randint(0, 60)
                )
            )
            products.append(product)
        
        return products
