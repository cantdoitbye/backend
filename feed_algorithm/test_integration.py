"""
Integration test script for the feed algorithm.
This script demonstrates the feed generation process and validates the results.
"""
import os
import sys
import json
import logging
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('feed_algorithm_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
import django
django.setup()

User = get_user_model()

class FeedAlgorithmIntegrationTest(TestCase):
    """Integration tests for the feed algorithm."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logger.info("Setting up test environment...")
        cls.client = Client()
        
        # Create test users
        cls.users = {}
        for i in range(1, 4):
            user = User.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                password=f'testpass{i}'
            )
            cls.users[f'user{i}'] = user
            logger.info(f"Created test user: {user.username}")
        
        # Log in as the first user
        cls.client.login(username='testuser1', password='testpass1')
    
    def test_feed_generation(self):
        """Test feed generation through the GraphQL API."""
        logger.info("Testing feed generation...")
        
        # Define the GraphQL query
        query = """
        query {
            generateFeed(size: 5) {
                success
                message
                items {
                    id
                    contentType
                    contentId
                    score
                    ranking
                }
                totalCount
                hasMore
                composition {
                    personalConnections
                    interestBased
                    trendingContent
                    discoveryContent
                    communityContent
                    productContent
                }
            }
        }
        """
        
        # Make the request
        response = self.client.post(
            '/graphql/',
            {'query': query},
            content_type='application/json'
        )
        
        # Check the response status
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Log the response
        logger.info("Feed generation response:")
        logger.info(json.dumps(data, indent=2))
        
        # Check the response structure
        self.assertIn('data', data)
        self.assertIn('generateFeed', data['data'])
        feed_data = data['data']['generateFeed']
        
        # Validate the response
        self.assertTrue(feed_data['success'])
        self.assertIsInstance(feed_data['items'], list)
        self.assertLessEqual(len(feed_data['items']), 5)
        
        # Print results in a nice format
        print("\n" + "="*50)
        print("FEED GENERATION TEST RESULTS")
        print("="*50)
        print(f"Status: {'SUCCESS' if feed_data['success'] else 'FAILED'}")
        print(f"Message: {feed_data.get('message', 'No message')}")
        print(f"Items returned: {len(feed_data['items'])}")
        
        if feed_data['items']:
            print("\nFeed Items:")
            for idx, item in enumerate(feed_data['items'], 1):
                print(f"\n{idx}. {item['contentType'].upper()} (Score: {item['score']:.2f})")
                print(f"   ID: {item['contentId']}")
                print(f"   Ranking: {item['ranking']}")
        
        print("\nFeed Composition:")
        for key, value in feed_data['composition'].items():
            print(f"- {key}: {value*100:.1f}%")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    import unittest
    unittest.main()
