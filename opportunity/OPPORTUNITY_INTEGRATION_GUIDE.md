# 🚀 Opportunity Module - Complete Integration Guide

This guide provides step-by-step instructions to integrate the Opportunity module into your Ooumph platform.

---

## 📋 Table of Contents

1. [Files to Create](#files-to-create)
2. [Django Settings Updates](#django-settings-updates)
3. [Neo4j Indexes](#neo4j-indexes)
4. [GraphQL Schema Integration](#graphql-schema-integration)
5. [Feed Algorithm Integration](#feed-algorithm-integration)
6. [Notification Templates](#notification-templates)
7. [Users Model Update](#users-model-update)
8. [Testing](#testing)
9. [API Examples](#api-examples)

---

## 1. Files to Create

Copy all files from the `opportunity_module/` directory to your project:

```bash
# Create the opportunity app directory
mkdir -p opportunity/graphql

# Copy all files
cp opportunity_module/__init__.py opportunity/
cp opportunity_module/apps.py opportunity/
cp opportunity_module/models.py opportunity/

cp opportunity_module/graphql/__init__.py opportunity/graphql/
cp opportunity_module/graphql/types.py opportunity/graphql/
cp opportunity_module/graphql/inputs.py opportunity/graphql/
cp opportunity_module/graphql/mutations.py opportunity/graphql/
cp opportunity_module/graphql/queries.py opportunity/graphql/
```

---

## 2. Django Settings Updates

### A. Add to INSTALLED_APPS

**File:** `settings/base.py`

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'opportunity',  # Add this line
]
```

---

## 3. Neo4j Indexes

Create indexes for better query performance. Run these in Neo4j Browser or through Django shell:

```cypher
# Opportunity indexes
CREATE INDEX opportunity_uid IF NOT EXISTS FOR (o:Opportunity) ON (o.uid);
CREATE INDEX opportunity_role IF NOT EXISTS FOR (o:Opportunity) ON (o.role);
CREATE INDEX opportunity_job_type IF NOT EXISTS FOR (o:Opportunity) ON (o.job_type);
CREATE INDEX opportunity_location IF NOT EXISTS FOR (o:Opportunity) ON (o.location);
CREATE INDEX opportunity_is_active IF NOT EXISTS FOR (o:Opportunity) ON (o.is_active);
CREATE INDEX opportunity_is_deleted IF NOT EXISTS FOR (o:Opportunity) ON (o.is_deleted);
CREATE INDEX opportunity_created_at IF NOT EXISTS FOR (o:Opportunity) ON (o.created_at);

# For salary range queries
CREATE INDEX opportunity_salary_min IF NOT EXISTS FOR (o:Opportunity) ON (o.salary_min);
CREATE INDEX opportunity_salary_max IF NOT EXISTS FOR (o:Opportunity) ON (o.salary_max);
```

**Via Django Shell:**

```python
python manage.py shell

from neomodel import db

# Create all indexes
indexes = [
    "CREATE INDEX opportunity_uid IF NOT EXISTS FOR (o:Opportunity) ON (o.uid)",
    "CREATE INDEX opportunity_role IF NOT EXISTS FOR (o:Opportunity) ON (o.role)",
    "CREATE INDEX opportunity_job_type IF NOT EXISTS FOR (o:Opportunity) ON (o.job_type)",
    "CREATE INDEX opportunity_location IF NOT EXISTS FOR (o:Opportunity) ON (o.location)",
    "CREATE INDEX opportunity_is_active IF NOT EXISTS FOR (o:Opportunity) ON (o.is_active)",
    "CREATE INDEX opportunity_is_deleted IF NOT EXISTS FOR (o:Opportunity) ON (o.is_deleted)",
    "CREATE INDEX opportunity_created_at IF NOT EXISTS FOR (o:Opportunity) ON (o.created_at)",
    "CREATE INDEX opportunity_salary_min IF NOT EXISTS FOR (o:Opportunity) ON (o.salary_min)",
    "CREATE INDEX opportunity_salary_max IF NOT EXISTS FOR (o:Opportunity) ON (o.salary_max)",
]

for index in indexes:
    db.cypher_query(index)
    print(f"Created: {index}")
```

---

## 4. GraphQL Schema Integration

### A. Update Main Schema

**File:** `schema/schema.py`

```python
# Add import at top
from opportunity.graphql.queries import OpportunityQueries
from opportunity.graphql.mutations import OpportunityMutations

# Update Query class
class Query(
    # ... existing queries ...
    OpportunityQueries,  # Add this line
    graphene.ObjectType
):
    pass

# Update Mutation class
class Mutation(
    # ... existing mutations ...
    OpportunityMutations,  # Add this line
    graphene.ObjectType
):
    pass
```

---

## 5. Feed Algorithm Integration

To show opportunities in the feed alongside posts and debates, update the feed algorithm:

### A. Create Feed Union Type

**File:** `post/graphql/types.py` (or create `feed/graphql/types.py`)

Add this BEFORE existing type definitions:

```python
from opportunity.graphql.types import OpportunityType

class FeedItemType(graphene.Union):
    """
    Union type for mixed feed content.
    
    Allows feed to return posts, debates, and opportunities together.
    Frontend can render appropriate UI based on __typename.
    """
    class Meta:
        types = (PostType, OpportunityType)
    
    @classmethod
    def resolve_type(cls, instance, info):
        """Determine the type of feed item"""
        from opportunity.models import Opportunity
        from post.models import Post
        
        if isinstance(instance, Opportunity):
            return OpportunityType
        elif isinstance(instance, Post):
            return PostType
        return None


class FeedType(graphene.ObjectType):
    """Paginated feed with mixed content"""
    items = graphene.List(FeedItemType)
    total_count = graphene.Int()
    has_more = graphene.Boolean()
    offset = graphene.Int()
```

### B. Update Feed Query

**File:** `post/graphql/query.py` (or wherever your feed query is)

Add this new feed query method:

```python
@login_required
def resolve_mixed_feed(self, info, limit=20, offset=0):
    """
    Fetch mixed feed with posts, debates, and opportunities.
    
    This replaces or complements existing feed queries to include opportunities.
    """
    try:
        user = info.context.user
        current_user = Users.nodes.get(user_id=user.id)
        
        # Fetch posts and debates (existing logic)
        posts_query = """
        MATCH (post:Post {is_deleted: false})
        MATCH (creator:Users)-[:CREATED_BY]->(post)
        RETURN post, creator, 'post' as content_type
        ORDER BY post.created_at DESC
        LIMIT 10
        """
        
        # Fetch opportunities
        opps_query = """
        MATCH (opp:Opportunity {is_deleted: false, is_active: true})
        MATCH (creator:Users)-[:CREATED_BY]->(opp)
        RETURN opp, creator, 'opportunity' as content_type
        ORDER BY opp.created_at DESC
        LIMIT 10
        """
        
        # Execute queries
        from neomodel import db
        post_results, _ = db.cypher_query(posts_query)
        opp_results, _ = db.cypher_query(opps_query)
        
        # Combine and sort by created_at
        all_items = []
        
        for record in post_results:
            post = Post.inflate(record[0])
            all_items.append({
                'item': post,
                'created_at': post.created_at,
                'type': 'post'
            })
        
        for record in opp_results:
            opp = Opportunity.inflate(record[0])
            all_items.append({
                'item': opp,
                'created_at': opp.created_at,
                'type': 'opportunity'
            })
        
        # Sort by created_at
        all_items.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply pagination
        paginated_items = all_items[offset:offset + limit]
        
        # Convert to GraphQL types
        feed_items = []
        for item_data in paginated_items:
            item = item_data['item']
            if item_data['type'] == 'opportunity':
                feed_items.append(OpportunityType.from_neomodel(item, info, user))
            else:
                feed_items.append(PostType.from_neomodel(item, info))
        
        return FeedType(
            items=feed_items,
            total_count=len(all_items),
            has_more=(offset + limit) < len(all_items),
            offset=offset
        )
        
    except Exception as e:
        print(f"Error fetching mixed feed: {e}")
        raise GraphQLError("Failed to fetch feed")
```

### C. Add to Query Class

```python
class Query(graphene.ObjectType):
    # ... existing queries ...
    
    mixed_feed = graphene.Field(
        FeedType,
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        description="Fetch mixed feed with posts and opportunities"
    )
    
    # Add resolver
    resolve_mixed_feed = resolve_mixed_feed  # The function we created above
```

---

## 6. Notification Templates

### A. Add Opportunity Notification Templates

**File:** `notification/notification_templates.py`

Add the opportunity templates from `opportunity/notification_templates.py`:

```python
# At the end of NOTIFICATION_TEMPLATES dictionary, add:

# ========== OPPORTUNITY NOTIFICATIONS ==========
"new_opportunity_posted": {
    "title": "{username} posted a new job opportunity",
    "body": "{role} at {location} ({job_type})",
    "click_action": "opportunity_detail",
    "data_fields": ["username", "role", "location", "job_type", "opportunity_id"],
    "deep_link": "ooumph://opportunity/{opportunity_id}",
    "priority": "normal"
},

"opportunity_comment": {
    "title": "{username} commented on your job posting",
    "body": "{comment_preview}",
    "click_action": "opportunity_detail",
    "data_fields": ["username", "comment_preview", "opportunity_id", "comment_id"],
    "deep_link": "ooumph://opportunity/{opportunity_id}?comment={comment_id}",
    "priority": "high"
},

"opportunity_like": {
    "title": "{username} liked your job posting",
    "body": "{role} - {location}",
    "click_action": "opportunity_detail",
    "data_fields": ["username", "role", "location", "opportunity_id"],
    "deep_link": "ooumph://opportunity/{opportunity_id}",
    "priority": "normal"
},

"opportunity_share": {
    "title": "{username} shared your job posting",
    "body": "{role} at {location}",
    "click_action": "opportunity_detail",
    "data_fields": ["username", "role", "location", "opportunity_id"],
    "deep_link": "ooumph://opportunity/{opportunity_id}",
    "priority": "normal"
},
```

---

## 7. Users Model Update

Add relationship from Users to Opportunities:

**File:** `auth_manager/models.py`

Find the Users class and add this relationship:

```python
class Users(DjangoNode, StructuredNode):
    # ... existing fields ...
    
    # Add this line after other relationships
    opportunity = RelationshipFrom('opportunity.models.Opportunity', 'CREATED_BY')
```

---

## 8. Testing

### A. Test Opportunity Creation

```python
python manage.py shell

from opportunity.models import Opportunity
from auth_manager.models import Users

# Get a test user
user = Users.nodes.first()

# Create test opportunity
opp = Opportunity(
    role="Senior Django Developer",
    job_type="Full-Time",
    location="Remote",
    is_remote=True,
    experience_level="5+ years",
    salary_range_text="$120k-$160k USD",
    salary_min=120000,
    salary_max=160000,
    salary_currency="USD",
    description="We're looking for an experienced Django developer...",
    key_responsibilities=["Build scalable APIs", "Design database schemas"],
    requirements=["5+ years Django", "Strong Python skills"],
    skills=["Django", "Python", "PostgreSQL", "Redis"],
    cta_text="Apply Now",
    is_active=True
)
opp.save()

# Connect to user
opp.created_by.connect(user)

print(f"Created opportunity: {opp.uid}")
```

### B. Test GraphQL Queries

```graphql
# 1. Create Opportunity
mutation {
  createOpportunity(input: {
    role: "UI/UX Designer"
    jobType: "Full-Time"
    location: "Bengaluru, Hybrid"
    experienceLevel: "2-4 years"
    description: "We're seeking a talented UI/UX designer..."
    keyResponsibilities: [
      "Create wireframes and prototypes"
      "Collaborate with developers"
    ]
    requirements: [
      "2+ years UI/UX experience"
      "Proficiency in Figma"
    ]
    skills: ["Figma", "UX Research", "Prototyping"]
    salaryRangeText: "₹6-₹10 LPA"
    salaryMin: 600000
    salaryMax: 1000000
    isHybrid: true
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

# 2. Fetch Opportunities
query {
  opportunities(filter: {
    jobType: "Full-Time"
    isRemote: false
    limit: 10
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
      }
    }
    totalCount
    hasMore
  }
}

# 3. Fetch Single Opportunity
query {
  opportunity(uid: "opportunity_uid_here") {
    uid
    role
    jobType
    location
    description
    keyResponsibilities
    requirements
    skills
    likeCount
    commentCount
    createdBy {
      username
      profilePicture
    }
  }
}

# 4. Mixed Feed
query {
  mixedFeed(limit: 20, offset: 0) {
    items {
      __typename
      ... on PostType {
        uid
        postTitle
        postText
      }
      ... on OpportunityType {
        uid
        role
        location
        salaryRangeText
      }
    }
    totalCount
    hasMore
  }
}
```

---

## 9. API Examples

### Frontend AI Chatbot Integration

```javascript
// After AI conversation completes and user clicks "Post it!"

const createOpportunity = async (opportunityData) => {
  const mutation = `
    mutation CreateOpportunity($input: CreateOpportunityInput!) {
      createOpportunity(input: $input) {
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
  `;

  const variables = {
    input: {
      role: opportunityData.role,
      jobType: opportunityData.jobType,
      location: opportunityData.location,
      experienceLevel: opportunityData.experienceLevel,
      description: opportunityData.description,
      keyResponsibilities: opportunityData.keyResponsibilities,
      requirements: opportunityData.requirements,
      skills: opportunityData.skills,
      salaryRangeText: opportunityData.salaryRangeText,
      salaryMin: opportunityData.salaryMin,
      salaryMax: opportunityData.salaryMax,
      isHybrid: opportunityData.isHybrid,
      isRemote: opportunityData.isRemote,
      documentIds: opportunityData.documentIds,
      coverImageId: opportunityData.coverImageId,
      ctaText: opportunityData.ctaText || "Apply Now",
      privacy: "public"
    }
  };

  try {
    const response = await fetch('/graphql', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ query: mutation, variables })
    });

    const result = await response.json();
    
    if (result.data.createOpportunity.success) {
      console.log('Opportunity created:', result.data.createOpportunity.opportunity);
      // Navigate to opportunity detail or feed
    } else {
      console.error('Error:', result.data.createOpportunity.message);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

---

## ✅ Verification Checklist

- [ ] All files copied to `opportunity/` directory
- [ ] `opportunity` added to INSTALLED_APPS
- [ ] Neo4j indexes created
- [ ] GraphQL schema updated with OpportunityQueries and OpportunityMutations
- [ ] Feed algorithm updated to include opportunities (optional but recommended)
- [ ] Notification templates added
- [ ] Users model updated with opportunity relationship
- [ ] Test opportunity created successfully via Django shell
- [ ] Test GraphQL mutations work in GraphiQL/Postman
- [ ] Test GraphQL queries return data
- [ ] Notifications sent when opportunity is created

---

## 🎯 Next Steps

1. **Frontend Implementation:**
   - Build AI chatbot UI for opportunity creation
   - Create opportunity card component for feed
   - Add opportunity detail view
   - Implement search/filter UI

2. **Future Enhancements:**
   - Applicant tracking system (Application model)
   - Email notifications to applicants
   - Opportunity analytics dashboard
   - Automatic expiry handling (celery task)
   - AI-powered job matching

3. **Testing:**
   - Write unit tests for models
   - Write integration tests for mutations
   - Test notification delivery
   - Load testing for feed queries

---

## 🐛 Troubleshooting

**Problem: "Opportunity model not found"**
- Solution: Make sure `opportunity` is in INSTALLED_APPS and Django server is restarted

**Problem: "GraphQL mutation not found"**
- Solution: Verify schema.py has OpportunityMutations imported and added to Mutation class

**Problem: "Notifications not sending"**
- Solution: Check GlobalNotificationService is working, templates are added, and users have device_ids

**Problem: "Feed not showing opportunities"**
- Solution: Verify mixed_feed query is implemented and FeedItemType union is configured correctly

---

## 📞 Support

For issues or questions, check:
1. Django logs: `docker logs hey_backend`
2. Neo4j Browser: Verify nodes are created
3. GraphiQL: Test queries directly
4. Notification logs: Check if notifications are being sent

---

**🚀 You're all set! The Opportunity module is ready to use.**
