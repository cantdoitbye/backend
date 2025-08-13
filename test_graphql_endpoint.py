#!/usr/bin/env python3
"""
Test script to verify GraphQL endpoint is working with agentic APIs
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{BASE_URL}/graphql"

def test_graphql_introspection():
    """Test GraphQL introspection to see available types and fields"""
    
    introspection_query = """
    query {
      __schema {
        queryType {
          fields {
            name
            description
          }
        }
        mutationType {
          fields {
            name
            description
          }
        }
      }
    }
    """
    
    response = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": introspection_query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Look for agentic-related queries and mutations
        queries = data.get("data", {}).get("__schema", {}).get("queryType", {}).get("fields", [])
        mutations = data.get("data", {}).get("__schema", {}).get("mutationType", {}).get("fields", [])
        
        agentic_queries = [f["name"] for f in queries if "agent" in f["name"].lower()]
        agentic_mutations = [f["name"] for f in mutations if "agent" in f["name"].lower()]
        
        print("✅ GraphQL endpoint is working!")
        print(f"🔍 Found {len(agentic_queries)} agentic queries:")
        for query_name in sorted(agentic_queries):
            print(f"   - {query_name}")
        print(f"🔧 Found {len(agentic_mutations)} agentic mutations:")
        for mutation_name in sorted(agentic_mutations):
            print(f"   - {mutation_name}")
        
        return len(agentic_queries) > 0 or len(agentic_mutations) > 0
    else:
        print(f"❌ GraphQL endpoint error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_simple_query():
    """Test a simple query to see if agentic queries are available"""
    
    # Test query to check available queries
    query = """
    query {
      __type(name: "Query") {
        fields {
          name
          description
        }
      }
    }
    """
    
    response = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        fields = data.get("data", {}).get("__type", {}).get("fields", [])
        
        # Look for agentic queries
        agentic_queries = []
        for field in fields:
            field_name = field.get("name", "")
            if "agent" in field_name.lower():
                agentic_queries.append(field_name)
        
        print(f"🔍 Found {len(agentic_queries)} agentic queries:")
        for query_name in sorted(agentic_queries):
            print(f"   - {query_name}")
        
        return len(agentic_queries) > 0
    else:
        print(f"❌ Query test failed: {response.status_code}")
        return False

def test_mutations():
    """Test to see if agentic mutations are available"""
    
    query = """
    query {
      __type(name: "Mutation") {
        fields {
          name
          description
        }
      }
    }
    """
    
    response = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        fields = data.get("data", {}).get("__type", {}).get("fields", [])
        
        # Look for agentic mutations
        agentic_mutations = []
        for field in fields:
            field_name = field.get("name", "")
            if "agent" in field_name.lower():
                agentic_mutations.append(field_name)
        
        print(f"🔧 Found {len(agentic_mutations)} agentic mutations:")
        for mutation_name in sorted(agentic_mutations):
            print(f"   - {mutation_name}")
        
        return len(agentic_mutations) > 0
    else:
        print(f"❌ Mutation test failed: {response.status_code}")
        return False

def main():
    print("🧪 Testing Agentic GraphQL Endpoint")
    print("=" * 50)
    
    try:
        # Test basic connectivity
        print("1. Testing GraphQL introspection...")
        introspection_ok = test_graphql_introspection()
        
        if not introspection_ok:
            print("❌ GraphQL endpoint is not working properly")
            return
        
        print("\n2. Testing available queries...")
        queries_ok = test_simple_query()
        
        print("\n3. Testing available mutations...")
        mutations_ok = test_mutations()
        
        print("\n" + "=" * 50)
        if queries_ok and mutations_ok:
            print("🎉 SUCCESS: Agentic APIs are available!")
            print("📝 You can now use the APIs in Postman or GraphQL playground")
            print(f"🌐 GraphQL Playground: {BASE_URL}/graphql")
        else:
            print("⚠️  WARNING: Some agentic APIs may not be properly registered")
            print("   Check the Django server logs for any import errors")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Django server")
        print("   Make sure the server is running: python manage.py runserver")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()