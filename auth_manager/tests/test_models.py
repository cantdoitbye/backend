# auth_manager/tests/test_models.py

from django.test import TestCase
from auth_manager.models import Users
from neomodel import db

class UsersModelTest(TestCase):

    def setUp(self):
        # Clean up the Users nodes in the database before each test
        db.cypher_query("MATCH (n:Users) DETACH DELETE n")
    
    def test_create_users_node(self):
        # Create a new Users node
        user_meta = Users(user_id='1', username='testuser', email='testuser@example.com')
        user_meta.save()
        
        # Retrieve the Users node
        retrieved_user_meta = Users.nodes.get(user_id='1')
        
        self.assertIsNotNone(retrieved_user_meta)
        self.assertEqual(retrieved_user_meta.username, 'testuser')
        self.assertEqual(retrieved_user_meta.email, 'testuser@example.com')

    def test_update_users_node(self):
        # Create a new Users node
        user_meta = Users(user_id='1', username='testuser', email='testuser@example.com')
        user_meta.save()
        
        # Update the Users node
        user_meta.username = 'updateduser'
        user_meta.email = 'updateduser@example.com'
        user_meta.save()
        
        # Retrieve the updated Users node
        updated_user_meta = Users.nodes.get(user_id='1')
        
        self.assertIsNotNone(updated_user_meta)
        self.assertEqual(updated_user_meta.username, 'updateduser')
        self.assertEqual(updated_user_meta.email, 'updateduser@example.com')

    def test_create_users_node_only_once(self):
        # Create a new Users node
        user_meta = Users(user_id='1', username='testuser', email='testuser@example.com')
        user_meta.save()
        
        # Attempt to create another Users node with the same user_id
        with self.assertRaises(Exception):
            Users(user_id='1', username='anotheruser', email='anotheruser@example.com').save()
