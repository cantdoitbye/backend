from django.test import TestCase
from django.contrib.auth.models import User
from auth_manager.models import Users
from neomodel import db

class UserMetaDataSignalTest(TestCase):

    def setUp(self):
        # Clean up the Users nodes in the database before each test
        db.cypher_query("MATCH (n:Users) DETACH DELETE n")
    
    def test_create_user_creates_users_node(self):
        # Create a new User instance
        user = User.objects.create(username='testuser', email='testuser@example.com')
        
        # Check if a Users node is created in Neo4j
        user_meta = Users.nodes.get(user_id=str(user.id))
        
        self.assertIsNotNone(user_meta)
        self.assertEqual(user_meta.username, 'testuser')
        self.assertEqual(user_meta.email, 'testuser@example.com')

    def test_update_user_updates_users_node(self):
        # Create a new User instance
        user = User.objects.create(username='testuser', email='testuser@example.com')
        
        # Update the User instance
        user.username = 'updateduser'
        user.email = 'updateduser@example.com'
        user.save()
        
        # Check if the Users node is updated in Neo4j
        user_meta = Users.nodes.get(user_id=str(user.id))
        
        self.assertIsNotNone(user_meta)
        self.assertEqual(user_meta.username, 'updateduser')
        self.assertEqual(user_meta.email, 'updateduser@example.com')

    def test_create_user_creates_users_node_only_once(self):
        # Create a new User instance
        user = User.objects.create(username='testuser', email='testuser@example.com')
        
        # Check if a Users node is created only once
        users_nodes_count = len(Users.nodes.filter(user_id=str(user.id)))
        
        self.assertEqual(users_nodes_count, 1)
