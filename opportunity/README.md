# 🎯 Opportunity Module - Complete Package

**AI-Driven Job Opportunity Creation & Management for Ooumph Platform**

---

## 📦 Package Contents

This package contains everything needed to add job opportunity functionality to your Ooumph platform:

### Core Files
- `__init__.py` - Module initialization
- `apps.py` - Django app configuration
- `models.py` - Neo4j Opportunity model (130+ lines)
- `tests.py` - Comprehensive test suite

### GraphQL API
- `graphql/__init__.py` - GraphQL package init
- `graphql/types.py` - OpportunityType and FeedType definitions
- `graphql/inputs.py` - Input validation types
- `graphql/mutations.py` - Create, Update, Delete mutations
- `graphql/queries.py` - Fetch and filter queries

### Integration & Documentation
- `notification_templates.py` - Notification templates for opportunity events
- `OPPORTUNITY_INTEGRATION_GUIDE.md` - Step-by-step integration instructions
- `README.md` - This file

---

## ✨ Features

### 1. **AI-Driven Creation**
- Conversational interface for opportunity posting
- AI-generated descriptions and requirements
- Document attachment support (JDs, company decks)
- Cover image upload

### 2. **Structured Data Model**
- Role and job type
- Location (remote, hybrid, on-site)
- Experience level
- Salary range (text + numeric for filtering)
- Key responsibilities list
- Requirements list
- Skills list
- Good-to-have skills

### 3. **Feed Integration**
- Shows alongside posts and debates
- Supports all engagement actions (likes, comments, shares)
- Privacy controls
- Feed algorithm compatible

### 4. **Search & Filter**
- Search by keywords
- Filter by job type, location, salary
- Remote/hybrid filters
- Skills matching
- Sorting options

### 5. **Notifications**
- New opportunity posted
- Comments on opportunities
- Likes and shares
- Mentions in opportunities

### 6. **Management**
- Update opportunity details
- Close/reopen opportunities
- Set expiry dates
- Track engagement metrics

---

## 🚀 Quick Start

### 1. Copy Files
```bash
# Copy all files to your project
cp -r opportunity_module/* opportunity/
```

### 2. Update Settings
```python
# settings/base.py
INSTALLED_APPS = [
    # ... existing apps ...
    'opportunity',
]
```

### 3. Update Schema
```python
# schema/schema.py
from opportunity.graphql.queries import OpportunityQueries
from opportunity.graphql.mutations import OpportunityMutations

class Query(OpportunityQueries, ...):
    pass

class Mutation(OpportunityMutations, ...):
    pass
```

### 4. Create Indexes
```python
python manage.py shell
from neomodel import db

indexes = [
    "CREATE INDEX opportunity_uid IF NOT EXISTS FOR (o:Opportunity) ON (o.uid)",
    "CREATE INDEX opportunity_role IF NOT EXISTS FOR (o:Opportunity) ON (o.role)",
    "CREATE INDEX opportunity_is_active IF NOT EXISTS FOR (o:Opportunity) ON (o.is_active)",
]

for index in indexes:
    db.cypher_query(index)
```

### 5. Test
```bash
python manage.py test opportunity
```

---

## 📝 Usage Examples

### GraphQL: Create Opportunity
```graphql
mutation {
  createOpportunity(input: {
    role: "Senior Backend Developer"
    jobType: "Full-Time"
    location: "San Francisco, Hybrid"
    experienceLevel: "5+ years"
    description: "We're looking for an experienced backend developer..."
    keyResponsibilities: [
      "Design and implement scalable APIs"
      "Mentor junior developers"
      "Optimize database queries"
    ]
    requirements: [
      "5+ years of backend development"
      "Strong Python and Django skills"
      "Experience with microservices"
    ]
    skills: ["Python", "Django", "PostgreSQL", "Redis", "Docker"]
    salaryRangeText: "$150k-$200k"
    salaryMin: 150000
    salaryMax: 200000
    isHybrid: true
    ctaText: "Apply Now"
  }) {
    success
    message
    opportunity {
      uid
      role
      location
      createdAt
    }
  }
}
```

### GraphQL: Fetch Opportunities
```graphql
query {
  opportunities(filter: {
    jobType: "Full-Time"
    isRemote: true
    salaryMin: 100000
    skills: ["Python", "Django"]
    limit: 20
    offset: 0
  }) {
    opportunities {
      uid
      role
      location
      salaryRangeText
      skills
      createdBy {
        username
        profilePicture
      }
      likeCount
      commentCount
    }
    totalCount
    hasMore
  }
}
```

### Python: Create Opportunity Programmatically
```python
from opportunity.models import Opportunity
from auth_manager.models import Users

user = Users.nodes.get(user_id=1)

opp = Opportunity(
    role="Product Designer",
    job_type="Full-Time",
    location="Remote",
    is_remote=True,
    experience_level="3-5 years",
    description="Design amazing products",
    key_responsibilities=["Create user flows", "Design interfaces"],
    requirements=["3+ years design experience", "Figma proficiency"],
    skills=["Figma", "User Research", "Prototyping"],
    salary_range_text="$120k-$160k",
    salary_min=120000,
    salary_max=160000,
    is_active=True
)
opp.save()
opp.created_by.connect(user)
```

---

## 🏗️ Architecture

### Database Structure
```
Opportunity (Neo4j Node)
├── Core Fields: role, job_type, location
├── Experience: experience_level, salary_*
├── Content: description, key_responsibilities, requirements
├── Skills: skills, good_to_have_skills, tags
├── Media: document_ids, cover_image_id
├── Relationships:
│   ├── created_by → Users
│   ├── updated_by → Users
│   ├── like ← Like
│   ├── comment ← Comment
│   ├── share ← PostShare
│   ├── view ← PostView
│   └── saved ← SavedPost
└── Status: is_active, is_deleted, expires_at
```

### GraphQL Schema
```
Types:
- OpportunityType (full opportunity data)
- OpportunityListType (paginated list)
- FeedItemType (union of Post | Opportunity)

Inputs:
- CreateOpportunityInput
- UpdateOpportunityInput
- DeleteOpportunityInput
- OpportunityFilterInput

Mutations:
- createOpportunity
- updateOpportunity
- deleteOpportunity

Queries:
- opportunity(uid)
- opportunities(filter)
- myOpportunities
- userOpportunities(userUid)
```

---

## 🔌 Integration Points

### 1. Feed Algorithm
Opportunities integrate seamlessly with your existing feed:
- Same engagement mechanics (likes, comments, shares)
- Compatible with feed scoring algorithm
- Can be mixed with posts and debates
- Supports privacy settings

### 2. Notifications
Uses GlobalNotificationService for:
- New opportunity posted (to connections)
- Comments on opportunities
- Likes and shares
- Mentions in opportunities

### 3. Activity Tracking
Integrates with ActivityService:
- Track opportunity creation
- Track updates and closes
- Monitor engagement metrics

### 4. Search & Filter
Built-in filtering by:
- Keywords (role, description)
- Job type
- Location (with remote/hybrid)
- Salary range
- Skills
- Tags

---

## 📊 Model Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uid | String | Auto | Unique identifier |
| role | String | Yes | Job role/title |
| job_type | String | Yes | Full-Time, Part-Time, Contract, Internship |
| location | String | Yes | Location description |
| is_remote | Boolean | No | Fully remote position |
| is_hybrid | Boolean | No | Hybrid work model |
| experience_level | String | Yes | e.g., "2-4 years" |
| salary_range_text | String | No | Human-readable salary |
| salary_min | Integer | No | Minimum salary (for filtering) |
| salary_max | Integer | No | Maximum salary (for filtering) |
| salary_currency | String | No | Currency code (default: INR) |
| description | String | Yes | Full job description |
| key_responsibilities | Array | Yes | List of responsibilities |
| requirements | Array | Yes | List of requirements |
| good_to_have_skills | Array | No | Nice-to-have skills |
| skills | Array | Yes | Required skills |
| document_ids | Array | No | Attached documents |
| cover_image_id | String | No | Cover image |
| cta_text | String | No | CTA button text |
| cta_type | String | No | CTA type |
| privacy | String | No | Visibility setting |
| tags | Array | No | Additional tags |
| is_active | Boolean | No | Active status |
| is_deleted | Boolean | No | Soft delete flag |
| expires_at | DateTime | No | Expiry date |
| created_at | DateTime | Auto | Creation timestamp |
| updated_at | DateTime | Auto | Last update timestamp |

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test opportunity
```

### Test Specific Case
```bash
python manage.py test opportunity.tests.OpportunityModelTestCase
```

### Manual Testing (Django Shell)
```python
python manage.py shell

# Import models
from opportunity.models import Opportunity
from auth_manager.models import Users

# Get user
user = Users.nodes.first()

# Create opportunity
opp = Opportunity(
    role="Test Role",
    job_type="Full-Time",
    location="Test Location",
    experience_level="2-4 years",
    description="Test description",
    key_responsibilities=["Task 1", "Task 2"],
    requirements=["Req 1", "Req 2"],
    skills=["Skill 1", "Skill 2"]
)
opp.save()
opp.created_by.connect(user)

print(f"Created: {opp.uid}")

# Query opportunities
opps = Opportunity.nodes.filter(is_active=True, is_deleted=False)
for o in opps[:5]:
    print(f"{o.role} - {o.location}")
```

---

## 📚 Documentation

- **Full Integration Guide**: See `OPPORTUNITY_INTEGRATION_GUIDE.md`
- **Notification Templates**: See `notification_templates.py`
- **Test Cases**: See `tests.py`
- **Code Documentation**: All files have comprehensive docstrings

---

## 🔮 Future Enhancements

### Phase 2 (Applicant Tracking)
- Application model
- Application status workflow
- Applicant profiles
- Application analytics

### Phase 3 (Advanced Features)
- AI-powered job matching
- Salary benchmarking
- Automatic expiry handling (Celery)
- Email notifications
- Application chat/messaging
- Interview scheduling

### Phase 4 (Enterprise)
- Company profiles
- Team hiring
- ATS integrations
- Analytics dashboard
- Bulk import/export

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | Ensure `opportunity` in INSTALLED_APPS |
| GraphQL errors | Verify schema imports in schema.py |
| Notifications not sent | Check templates added, users have device_ids |
| Feed not showing opps | Implement mixed_feed query |
| Indexes not working | Run index creation commands |

---

## 📞 Support & Contact

For issues or questions:
1. Check integration guide
2. Review test cases
3. Check Docker logs: `docker logs hey_backend`
4. Verify Neo4j data in Browser

---

## ✅ Completion Checklist

- [x] Complete Neo4j model with relationships
- [x] Full GraphQL API (mutations + queries)
- [x] Notification integration
- [x] Feed integration support
- [x] Search and filter functionality
- [x] Privacy controls
- [x] Engagement metrics
- [x] Comprehensive documentation
- [x] Test suite
- [x] Integration guide

---

## 📄 License

This module is part of the Ooumph platform.

---

**Version**: 1.0.0  
**Created**: 2024  
**Status**: Production Ready ✅

---

## 🎉 You're All Set!

The Opportunity module is complete and ready for integration. Follow the integration guide to add it to your platform, then start creating job opportunities through the AI chatbot!

**Key Benefits:**
- ✅ Professional job posting system
- ✅ AI-assisted creation
- ✅ Seamless feed integration
- ✅ Full engagement support
- ✅ Advanced search/filter
- ✅ Production-ready code

**Enjoy building the future of professional networking! 🚀**
