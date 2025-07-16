import json
from django.test import TestCase
from graphene.test import Client
from auth_manager.models import Users
from story.graphql.schema import schema  

class CreateStoryTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = Users(
            uid="testuser",
            email="testuser@example.com",
            username="testuser",
            password="password"
        )
        self.user.save()

        # Set up the GraphQL client
        self.client = Client(schema)

    def test_create_story(self):
        # Define the mutation
        mutation = '''
        mutation CreateStory($title: String!, $content: String, $privacy: String) {
            createStory(title: $title, content: $content, privacy: $privacy) {
                story {
                    uid
                    title
                    content
                    privacy
                }
                success
            }
        }
        '''

        # Simulate an authenticated user
        context_value = {
            'user': self.user,
            'payload': {'user_id': self.user.uid}
        }

        # Execute the mutation
        response = self.client.execute(
            mutation,
            variables={
                'title': 'Test Story',
                'content': 'This is a test story.',
                'privacy': 'Universal'
            },
            context_value=context_value
        )

        # Parse the response content
        content = json.loads(json.dumps(response))

        # Assertions
        # self.assertIsNone(content.get('errors'))
        self.assertTrue(content['data']['createStory']['success'])
        # self.assertEqual(content['data']['createStory']['story']['title'], 'Test Story')
        # self.assertEqual(content['data']['createStory']['story']['content'], 'This is a test story.')
        # self.assertEqual(content['data']['createStory']['story']['privacy'], 'Universal')

        # Verify the story was saved in the database
        # created_story = Story.nodes.get(title='Test Story')
        # self.assertIsNotNone(created_story)
        # self.assertEqual(created_story.content, 'This is a test story.')
        # self.assertEqual(created_story.privacy, 'Universal')
        # self.assertEqual(created_story.created_by.single().uid, self.user.uid)


