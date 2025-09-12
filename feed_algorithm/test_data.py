""
Test data generation for the feed algorithm.
This script populates the database with sample data for testing.
"""
import os
import sys
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
import django
django.setup()

from feed_algorithm.models import UserProfile, FeedComposition
from post.models import Post  # Adjust import based on your actual model

User = get_user_model()

class TestDataGenerator:
    """Generates test data for the feed algorithm."""
    
    def __init__(self):
        self.users = []
        self.posts = []
        self.categories = [
            'technology', 'sports', 'entertainment', 'politics', 'science',
            'health', 'business', 'education', 'art', 'food'
        ]
    
    def generate_users(self, count=5):
        """Generate test users with profiles."""
        print(f"Generating {count} test users...")
        
        for i in range(1, count + 1):
            user = User.objects.create_user(
                username=f'testuser_{i}',
                email=f'test_{i}@example.com',
                password=f'testpass_{i}'
            )
            
            # Create user profile
            profile = UserProfile.objects.get(user=user)
            profile.content_language = random.choice(['en', 'es', 'fr', 'de'])
            profile.privacy_level = random.choice(['public', 'friends', 'private'])
            profile.save()
            
            # Create feed composition
            composition = FeedComposition.objects.get(user=user)
            # Randomize composition while ensuring it sums to 1.0
            values = [random.random() for _ in range(6)]
            total = sum(values)
            composition.personal_connections = round(values[0]/total, 2)
            composition.interest_based = round(values[1]/total, 2)
            composition.trending_content = round(values[2]/total, 2)
            composition.discovery_content = round(values[3]/total, 2)
            composition.community_content = round(values[4]/total, 2)
            composition.product_content = round(1 - sum([
                composition.personal_connections,
                composition.interest_based,
                composition.trending_content,
                composition.discovery_content,
                composition.community_content
            ]), 2)
            composition.save()
            
            self.users.append(user)
            print(f"Created user: {user.username} (ID: {user.id})")
    
    def generate_posts(self, count_per_user=5):
        """Generate test posts for each user."""
        if not self.users:
            print("No users found. Please generate users first.")
            return
        
        print(f"Generating {count_per_user} posts per user...")
        
        for user in self.users:
            for i in range(count_per_user):
                # Create posts with random dates in the last 30 days
                created_at = timezone.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                post = Post.objects.create(
                    author=user,
                    title=f"Post {i+1} by {user.username}",
                    content=f"This is a test post by {user.username}." * 5,
                    category=random.choice(self.categories),
                    is_published=True,
                    created_at=created_at,
                    updated_at=created_at
                )
                
                self.posts.append(post)
            print(f"Created {count_per_user} posts for {user.username}")
    
    def generate_interactions(self):
        """Generate interactions between users and posts."""
        if not self.users or not self.posts:
            print("Need both users and posts to generate interactions.")
            return
        
        print("Generating interactions...")
        
        interaction_types = ['like', 'comment', 'share', 'save']
        
        for user in self.users:
            # Each user interacts with a random subset of posts
            num_interactions = random.randint(5, min(20, len(self.posts)))
            interacted_posts = random.sample(self.posts, num_interactions)
            
            for post in interacted_posts:
                # Skip if user is the author
                if post.author == user:
                    continue
                
                # Random interaction type
                interaction_type = random.choices(
                    interaction_types,
                    weights=[0.5, 0.3, 0.1, 0.1],  # Weighted probabilities
                    k=1
                )[0]
                
                # Create interaction
                # Note: Adjust this based on your actual interaction model
                interaction = {
                    'user': user,
                    'post': post,
                    'interaction_type': interaction_type,
                    'created_at': post.created_at + timedelta(
                        minutes=random.randint(1, 60*24*7)  # Within a week of post creation
                    )
                }
                
                # Save interaction (implementation depends on your models)
                try:
                    # Example: If you have an Interaction model
                    from interactions.models import Interaction
                    Interaction.objects.create(**interaction)
                except ImportError:
                    # Fallback if Interaction model doesn't exist
                    pass
                
            print(f"Generated interactions for {user.username}")
    
    def run(self, user_count=5, posts_per_user=5):
        """Run the test data generation process."""
        print("="*50)
        print("GENERATING TEST DATA FOR FEED ALGORITHM")
        print("="*50)
        
        self.generate_users(user_count)
        self.generate_posts(posts_per_user)
        self.generate_interactions()
        
        print("\nTest data generation complete!")
        print("You can now test the feed algorithm with the generated data.")

if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.run(user_count=5, posts_per_user=5)
