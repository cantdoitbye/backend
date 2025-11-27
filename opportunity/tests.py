# opportunity/tests.py

"""
Test Suite for Opportunity Module.

This module contains unit tests and integration tests for opportunity
creation, updates, queries, and interactions.

Run tests with: python manage.py test opportunity
"""

from django.test import TestCase
from graphene.test import Client
from neomodel import db, clear_neo4j_database
from unittest.mock import patch, MagicMock

from opportunity.models import Opportunity
from auth_manager.models import Users
from schema.schema import schema


class OpportunityModelTestCase(TestCase):
    """Test cases for Opportunity model"""
    
    def setUp(self):
        """Set up test data"""
        # Clear Neo4j test database
        # clear_neo4j_database(db)  # Uncomment for isolated tests
        
        # Create test user
        self.user = Users(
            user_id=1,
            username="testuser",
            email="test@example.com"
        )
        self.user.save()
    
    def tearDown(self):
        """Clean up after tests"""
        # Delete test data
        try:
            self.user.delete()
        except:
            pass
    
    def test_create_opportunity(self):
        """Test basic opportunity creation"""
        opp = Opportunity(
            role="Software Engineer",
            job_type="Full-Time",
            location="Remote",
            is_remote=True,
            experience_level="3-5 years",
            salary_range_text="$100k-$150k",
            salary_min=100000,
            salary_max=150000,
            description="We're hiring!",
            key_responsibilities=["Build features", "Write tests"],
            requirements=["Python", "Django"],
            skills=["Python", "Django", "PostgreSQL"],
            is_active=True
        )
        opp.save()
        
        self.assertIsNotNone(opp.uid)
        self.assertEqual(opp.role, "Software Engineer")
        self.assertTrue(opp.is_remote)
        
        # Clean up
        opp.delete()
    
    def test_opportunity_relationships(self):
        """Test opportunity creator relationship"""
        opp = Opportunity(
            role="Product Manager",
            job_type="Full-Time",
            location="San Francisco",
            experience_level="5+ years",
            description="Lead product strategy",
            key_responsibilities=["Define roadmap"],
            requirements=["5+ years PM experience"],
            skills=["Product Strategy", "Analytics"]
        )
        opp.save()
        
        # Connect to user
        opp.created_by.connect(self.user)
        
        # Verify relationship
        creator = opp.created_by.single()
        self.assertEqual(creator.uid, self.user.uid)
        
        # Clean up
        opp.delete()
    
    def test_engagement_score(self):
        """Test engagement score calculation"""
        opp = Opportunity(
            role="Data Scientist",
            job_type="Full-Time",
            location="New York",
            experience_level="2-4 years",
            description="Analyze data",
            key_responsibilities=["Build models"],
            requirements=["ML experience"],
            skills=["Python", "TensorFlow"]
        )
        opp.save()
        
        # Initial score should be 0
        self.assertEqual(opp.engagement_score, 0)
        
        # Clean up
        opp.delete()
    
    def test_close_opportunity(self):
        """Test closing an opportunity"""
        opp = Opportunity(
            role="Designer",
            job_type="Contract",
            location="Los Angeles",
            experience_level="1-3 years",
            description="Design interfaces",
            key_responsibilities=["Create mockups"],
            requirements=["Figma skills"],
            skills=["Figma", "UI Design"],
            is_active=True
        )
        opp.save()
        
        # Close opportunity
        opp.close_opportunity()
        
        self.assertFalse(opp.is_active)
        
        # Clean up
        opp.delete()


class OpportunityGraphQLTestCase(TestCase):
    """Test cases for Opportunity GraphQL API"""
    
    def setUp(self):
        """Set up GraphQL client and test data"""
        self.client = Client(schema)
        
        # Create test user
        self.user = Users(
            user_id=1,
            username="testuser",
            email="test@example.com"
        )
        self.user.save()
        
        # Mock authentication
        self.context = MagicMock()
        self.context.user = MagicMock()
        self.context.user.id = 1
        self.context.user.is_anonymous = False
        self.context.payload = {'user_id': 1}
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.user.delete()
        except:
            pass
    
    @patch('opportunity.graphql.mutations.get_valid_image')
    @patch('opportunity.graphql.mutations.transaction')
    def test_create_opportunity_mutation(self, mock_transaction, mock_get_valid_image):
        """Test createOpportunity mutation"""
        mock_get_valid_image.return_value = True
        mock_transaction.on_commit = lambda func: func()
        
        mutation = '''
            mutation {
                createOpportunity(input: {
                    role: "Backend Developer"
                    jobType: "Full-Time"
                    location: "Remote"
                    experienceLevel: "2-4 years"
                    description: "Build APIs"
                    keyResponsibilities: ["Design APIs", "Write tests"]
                    requirements: ["Django experience", "Python skills"]
                    skills: ["Python", "Django", "REST"]
                    salaryMin: 80000
                    salaryMax: 120000
                }) {
                    success
                    message
                    opportunity {
                        uid
                        role
                        location
                    }
                }
            }
        '''
        
        result = self.client.execute(mutation, context_value=self.context)
        
        self.assertIsNone(result.get('errors'))
        self.assertTrue(result['data']['createOpportunity']['success'])
        self.assertIsNotNone(result['data']['createOpportunity']['opportunity'])
    
    def test_opportunities_query(self):
        """Test opportunities query"""
        # Create test opportunity
        opp = Opportunity(
            role="Frontend Developer",
            job_type="Full-Time",
            location="Austin",
            experience_level="3-5 years",
            description="Build UIs",
            key_responsibilities=["Develop components"],
            requirements=["React experience"],
            skills=["React", "JavaScript"],
            is_active=True,
            is_deleted=False
        )
        opp.save()
        opp.created_by.connect(self.user)
        
        query = '''
            query {
                opportunities(filter: {
                    jobType: "Full-Time"
                    limit: 10
                }) {
                    opportunities {
                        uid
                        role
                        location
                    }
                    totalCount
                }
            }
        '''
        
        result = self.client.execute(query, context_value=self.context)
        
        self.assertIsNone(result.get('errors'))
        self.assertIsNotNone(result['data']['opportunities'])
        
        # Clean up
        opp.delete()
    
    def test_opportunity_query(self):
        """Test single opportunity query"""
        # Create test opportunity
        opp = Opportunity(
            role="DevOps Engineer",
            job_type="Full-Time",
            location="Seattle",
            experience_level="5+ years",
            description="Manage infrastructure",
            key_responsibilities=["Deploy services"],
            requirements=["AWS experience"],
            skills=["AWS", "Docker", "Kubernetes"],
            is_active=True,
            is_deleted=False
        )
        opp.save()
        opp.created_by.connect(self.user)
        
        query = f'''
            query {{
                opportunity(uid: "{opp.uid}") {{
                    uid
                    role
                    location
                    description
                }}
            }}
        '''
        
        result = self.client.execute(query, context_value=self.context)
        
        self.assertIsNone(result.get('errors'))
        self.assertEqual(result['data']['opportunity']['role'], "DevOps Engineer")
        
        # Clean up
        opp.delete()


class OpportunityFilterTestCase(TestCase):
    """Test cases for opportunity filtering and search"""
    
    def setUp(self):
        """Set up test opportunities"""
        self.user = Users(
            user_id=1,
            username="testuser",
            email="test@example.com"
        )
        self.user.save()
        
        # Create multiple test opportunities
        self.opportunities = []
        
        # Remote opportunity
        opp1 = Opportunity(
            role="Remote Developer",
            job_type="Full-Time",
            location="Remote",
            is_remote=True,
            experience_level="2-4 years",
            description="Work remotely",
            key_responsibilities=["Code"],
            requirements=["Experience"],
            skills=["Python"],
            salary_min=80000,
            salary_max=120000,
            is_active=True,
            is_deleted=False
        )
        opp1.save()
        opp1.created_by.connect(self.user)
        self.opportunities.append(opp1)
        
        # Hybrid opportunity
        opp2 = Opportunity(
            role="Hybrid Designer",
            job_type="Full-Time",
            location="San Francisco, Hybrid",
            is_hybrid=True,
            experience_level="3-5 years",
            description="Design hybrid",
            key_responsibilities=["Design"],
            requirements=["Portfolio"],
            skills=["Figma"],
            salary_min=100000,
            salary_max=150000,
            is_active=True,
            is_deleted=False
        )
        opp2.save()
        opp2.created_by.connect(self.user)
        self.opportunities.append(opp2)
    
    def tearDown(self):
        """Clean up test data"""
        for opp in self.opportunities:
            try:
                opp.delete()
            except:
                pass
        try:
            self.user.delete()
        except:
            pass
    
    def test_filter_by_remote(self):
        """Test filtering by remote status"""
        query = """
        MATCH (opp:Opportunity {is_remote: true, is_deleted: false, is_active: true})
        RETURN opp
        """
        results, _ = db.cypher_query(query)
        
        self.assertGreater(len(results), 0)
    
    def test_filter_by_salary_range(self):
        """Test filtering by salary range"""
        query = """
        MATCH (opp:Opportunity {is_deleted: false, is_active: true})
        WHERE opp.salary_min >= 90000 AND opp.salary_max <= 160000
        RETURN opp
        """
        results, _ = db.cypher_query(query)
        
        self.assertGreater(len(results), 0)


# ========== INTEGRATION TESTS ==========

class OpportunityNotificationTestCase(TestCase):
    """Test notification sending for opportunities"""
    
    @patch('opportunity.graphql.mutations.GlobalNotificationService')
    def test_notification_on_create(self, mock_notification_service):
        """Test that notifications are sent when opportunity is created"""
        # This would test the _send_notifications method
        # Implementation depends on your testing setup
        pass


class OpportunityFeedIntegrationTestCase(TestCase):
    """Test opportunity integration with feed"""
    
    def test_opportunity_in_feed(self):
        """Test that opportunities appear in mixed feed"""
        # Create test opportunity
        # Query mixed feed
        # Verify opportunity appears
        pass


# ========== MANUAL TEST SCRIPTS ==========
"""
Run these manually in Django shell for quick testing:

python manage.py shell

# Test 1: Create Opportunity
from opportunity.models import Opportunity
from auth_manager.models import Users

user = Users.nodes.first()
opp = Opportunity(
    role="Test Engineer",
    job_type="Full-Time",
    location="Test City",
    experience_level="2-4 years",
    description="Test description",
    key_responsibilities=["Test task 1", "Test task 2"],
    requirements=["Test req 1", "Test req 2"],
    skills=["Skill 1", "Skill 2"],
    is_active=True
)
opp.save()
opp.created_by.connect(user)
print(f"Created opportunity: {opp.uid}")

# Test 2: Query Opportunities
from opportunity.models import Opportunity
opps = Opportunity.nodes.filter(is_deleted=False, is_active=True)
for opp in opps[:5]:
    print(f"{opp.role} - {opp.location}")

# Test 3: Update Opportunity
from opportunity.models import Opportunity
opp = Opportunity.nodes.first()
opp.salary_min = 100000
opp.salary_max = 150000
opp.save()
print(f"Updated: {opp.role} - ${opp.salary_min}-${opp.salary_max}")

# Test 4: Close Opportunity
from opportunity.models import Opportunity
opp = Opportunity.nodes.first()
opp.close_opportunity()
print(f"Closed: {opp.role} - Active: {opp.is_active}")
"""
