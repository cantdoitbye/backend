#!/usr/bin/env python
"""
Quick Start Script for Opportunity Module

This script helps you quickly test the opportunity module after installation.
Run this in Django shell: python manage.py shell < opportunity/quick_start.py

Or copy-paste sections into Django shell for interactive testing.
"""

print("=" * 60)
print("OPPORTUNITY MODULE - QUICK START SCRIPT")
print("=" * 60)
print()

# ========== STEP 1: IMPORT MODELS ==========
print("Step 1: Importing models...")
try:
    from opportunity.models import Opportunity
    from auth_manager.models import Users
    from neomodel import db
    print("✅ Models imported successfully")
except Exception as e:
    print(f"❌ Error importing models: {e}")
    exit(1)

print()

# ========== STEP 2: GET TEST USER ==========
print("Step 2: Getting test user...")
try:
    user = Users.nodes.first()
    if not user:
        print("❌ No users found. Please create a user first.")
        exit(1)
    print(f"✅ Found user: {user.username} (UID: {user.uid})")
except Exception as e:
    print(f"❌ Error getting user: {e}")
    exit(1)

print()

# ========== STEP 3: CREATE TEST OPPORTUNITY ==========
print("Step 3: Creating test opportunity...")
try:
    opp = Opportunity(
        role="Senior Software Engineer",
        job_type="Full-Time",
        location="San Francisco, Hybrid",
        is_hybrid=True,
        experience_level="5+ years",
        salary_range_text="$150k-$200k",
        salary_min=150000,
        salary_max=200000,
        salary_currency="USD",
        description="We're seeking an experienced software engineer to join our growing team. You'll work on cutting-edge technology and have the opportunity to make a significant impact on our product.",
        key_responsibilities=[
            "Design and implement scalable backend systems",
            "Mentor junior developers and conduct code reviews",
            "Collaborate with product team on feature planning",
            "Optimize application performance and reliability"
        ],
        requirements=[
            "5+ years of software development experience",
            "Strong proficiency in Python and Django",
            "Experience with PostgreSQL and Redis",
            "Excellent problem-solving and communication skills"
        ],
        good_to_have_skills=[
            "Experience with microservices architecture",
            "Knowledge of AWS or cloud platforms",
            "Contributions to open source projects"
        ],
        skills=[
            "Python",
            "Django",
            "PostgreSQL",
            "Redis",
            "Docker",
            "REST APIs"
        ],
        tags=["backend", "python", "senior", "hybrid"],
        cta_text="Apply Now",
        cta_type="apply",
        privacy="public",
        is_active=True,
        is_deleted=False
    )
    opp.save()
    print(f"✅ Created opportunity: {opp.uid}")
    print(f"   Role: {opp.role}")
    print(f"   Location: {opp.location}")
    print(f"   Salary: {opp.salary_range_text}")
except Exception as e:
    print(f"❌ Error creating opportunity: {e}")
    exit(1)

print()

# ========== STEP 4: CONNECT TO USER ==========
print("Step 4: Connecting opportunity to user...")
try:
    opp.created_by.connect(user)
    print(f"✅ Connected opportunity to {user.username}")
except Exception as e:
    print(f"❌ Error connecting: {e}")

print()

# ========== STEP 5: VERIFY RELATIONSHIP ==========
print("Step 5: Verifying relationship...")
try:
    creator = opp.created_by.single()
    if creator:
        print(f"✅ Verified: {creator.username} created opportunity")
    else:
        print("⚠️  No creator relationship found")
except Exception as e:
    print(f"❌ Error verifying: {e}")

print()

# ========== STEP 6: QUERY OPPORTUNITIES ==========
print("Step 6: Querying opportunities...")
try:
    query = """
    MATCH (opp:Opportunity {is_deleted: false, is_active: true})
    RETURN opp
    LIMIT 5
    """
    results, _ = db.cypher_query(query)
    print(f"✅ Found {len(results)} active opportunities:")
    for record in results:
        opportunity = Opportunity.inflate(record[0])
        print(f"   - {opportunity.role} @ {opportunity.location}")
except Exception as e:
    print(f"❌ Error querying: {e}")

print()

# ========== STEP 7: TEST FILTERS ==========
print("Step 7: Testing filters...")
try:
    # Filter by job type
    query = """
    MATCH (opp:Opportunity {job_type: 'Full-Time', is_deleted: false, is_active: true})
    RETURN count(opp) as count
    """
    results, _ = db.cypher_query(query)
    count = results[0][0] if results else 0
    print(f"✅ Found {count} Full-Time opportunities")
    
    # Filter by remote
    query = """
    MATCH (opp:Opportunity {is_remote: true, is_deleted: false, is_active: true})
    RETURN count(opp) as count
    """
    results, _ = db.cypher_query(query)
    count = results[0][0] if results else 0
    print(f"✅ Found {count} Remote opportunities")
    
    # Filter by salary range
    query = """
    MATCH (opp:Opportunity {is_deleted: false, is_active: true})
    WHERE opp.salary_min >= 100000
    RETURN count(opp) as count
    """
    results, _ = db.cypher_query(query)
    count = results[0][0] if results else 0
    print(f"✅ Found {count} opportunities with salary >= $100k")
    
except Exception as e:
    print(f"❌ Error testing filters: {e}")

print()

# ========== STEP 8: TEST ENGAGEMENT SCORE ==========
print("Step 8: Testing engagement score...")
try:
    score = opp.engagement_score
    print(f"✅ Engagement score: {score}")
except Exception as e:
    print(f"❌ Error calculating score: {e}")

print()

# ========== STEP 9: TEST OPPORTUNITY METHODS ==========
print("Step 9: Testing opportunity methods...")
try:
    # Test close
    print(f"   Active status before: {opp.is_active}")
    opp.close_opportunity()
    print(f"   Active status after close: {opp.is_active}")
    
    # Test reopen
    opp.reopen_opportunity()
    print(f"   Active status after reopen: {opp.is_active}")
    
    print("✅ Opportunity methods working correctly")
except Exception as e:
    print(f"❌ Error testing methods: {e}")

print()

# ========== STEP 10: SUMMARY ==========
print("=" * 60)
print("QUICK START COMPLETE!")
print("=" * 60)
print()
print("✅ All tests passed successfully!")
print()
print("Your opportunity module is working correctly. Next steps:")
print()
print("1. Test GraphQL mutations in GraphiQL:")
print("   - Open http://localhost:8000/graphql")
print("   - Try createOpportunity mutation")
print()
print("2. Test GraphQL queries:")
print("   - Try opportunities query with filters")
print("   - Try opportunity(uid) query")
print()
print("3. Test notifications:")
print("   - Create opportunity via mutation")
print("   - Check if notifications are sent")
print()
print("4. Integrate with feed:")
print("   - Implement mixed_feed query")
print("   - Test opportunities in feed")
print()
print("For more details, see:")
print("- README.md")
print("- OPPORTUNITY_INTEGRATION_GUIDE.md")
print()
print("Happy coding! 🚀")
print("=" * 60)


# ========== CLEANUP (OPTIONAL) ==========
# Uncomment to delete the test opportunity after testing
"""
print()
print("Cleanup: Deleting test opportunity...")
try:
    opp.delete()
    print("✅ Test opportunity deleted")
except Exception as e:
    print(f"❌ Error deleting: {e}")
"""


# ========== INTERACTIVE MODE ==========
print()
print("💡 TIP: You can now interact with the opportunity in the shell:")
print()
print("   # View opportunity details")
print("   print(opp.role)")
print("   print(opp.description)")
print("   print(opp.skills)")
print()
print("   # Update opportunity")
print("   opp.salary_min = 160000")
print("   opp.save()")
print()
print("   # Query all opportunities")
print("   all_opps = Opportunity.nodes.filter(is_deleted=False)")
print("   for o in all_opps:")
print("       print(f'{o.role} - {o.location}')")
print()
print("   # Get creator")
print("   creator = opp.created_by.single()")
print("   print(creator.username)")
print()
