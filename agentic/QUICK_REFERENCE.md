# Agentic Community Management - Quick Reference

## 🚀 Quick Start

### Server Setup
```bash
# Activate virtual environment
source myenv/bin/activate

# Run server
python manage.py runserver

# GraphQL endpoint
http://localhost:8000/graphql
```

## 📋 Essential APIs for Development

### 1. Create & Assign Agent (Most Common Flow)
```graphql
# Step 1: Create Agent
mutation {
  create_agent(input: {
    name: "Community Bot",
    agent_type: "COMMUNITY_LEADER",
    capabilities: ["edit_community", "moderate_users", "send_messages"],
    created_by_uid: "user-123"
  }) {
    success
    agent { uid name }
  }
}

# Step 2: Assign to Community
mutation {
  assign_agent_to_community(input: {
    agent_uid: "agent-abc123",
    community_uid: "community-xyz789",
    role: "LEADER",
    assigned_by_uid: "user-123"
  }) {
    success
    assignment { uid }
  }
}
```

### 2. Get Community Information
```graphql
# Get community leader
query {
  get_community_leader(community_uid: "community-xyz789") {
    uid name capabilities status
  }
}

# Get all community agents
query {
  get_community_agents(community_uid: "community-xyz789") {
    uid name role status
  }
}
```

### 3. Agent Memory Operations
```graphql
# Store context
mutation {
  store_agent_context(input: {
    agent_uid: "agent-abc123",
    community_uid: "community-xyz789",
    context_data: {"user_count": 150, "active_topics": ["events", "rules"]},
    context_type: "CONTEXT"
  }) {
    success
  }
}

# Update conversation
mutation {
  update_conversation_history(input: {
    agent_uid: "agent-abc123",
    community_uid: "community-xyz789",
    conversation_data: [
      {"role": "user", "message": "Hello"},
      {"role": "agent", "message": "Hi! How can I help?"}
    ]
  }) {
    success
  }
}
```

## 🔧 Development Utilities

### Test Agent Creation
```python
# Python test script
from agentic.services.agent_service import AgentService

service = AgentService()
agent = service.create_agent(
    name="Test Agent",
    agent_type="COMMUNITY_LEADER",
    capabilities=["edit_community"],
    created_by_uid="test-user"
)
print(f"Created agent: {agent.uid}")
```

### Check Agent Status
```graphql
query {
  get_agent(uid: "agent-abc123") {
    uid
    name
    status
    capabilities
    created_date
  }
}
```

## 🎯 Common Use Cases

### 1. Auto-assign Agent to New Community
```python
# In community creation logic
def create_community_with_agent(community_data, creator_uid):
    # Create community first
    community = create_community(community_data)
    
    # Create and assign agent
    agent = agent_service.create_agent(
        name=f"{community.name} Assistant",
        agent_type="COMMUNITY_LEADER",
        capabilities=["edit_community", "moderate_users"],
        created_by_uid=creator_uid
    )
    
    assignment = agent_service.assign_agent_to_community(
        agent_uid=agent.uid,
        community_uid=community.uid,
        assigned_by_uid=creator_uid
    )
    
    return community, agent, assignment
```

### 2. Agent Permission Check
```python
# Check if agent can perform action
from agentic.services.auth_service import AgentAuthService

auth_service = AgentAuthService()
can_edit = auth_service.check_permission(
    agent_uid="agent-abc123",
    community_uid="community-xyz789",
    permission="edit_community"
)
```

### 3. Memory Retrieval
```python
# Get agent context
from agentic.services.memory_service import AgentMemoryService

memory_service = AgentMemoryService()
context = memory_service.retrieve_context(
    agent_uid="agent-abc123",
    community_uid="community-xyz789"
)
```

## 🔍 Debugging & Monitoring

### Check Agent Assignments
```graphql
query {
  get_agent_assignments(agent_uid: "agent-abc123") {
    uid
    community_uid
    role
    status
    assigned_date
  }
}
```

### View Action History
```graphql
query {
  get_agent_action_history(input: {
    agent_uid: "agent-abc123",
    community_uid: "community-xyz789",
    limit: 10
  }) {
    success
    history
  }
}
```

### Memory Statistics
```graphql
query {
  get_memory_stats(input: {
    agent_uid: "agent-abc123"
  }) {
    success
    stats
  }
}
```

## ⚡ Performance Tips

1. **Batch Operations**: Use bulk mutations for multiple agents
2. **Memory Cleanup**: Regularly clean expired memory
3. **Pagination**: Use pagination for large result sets
4. **Caching**: Cache frequently accessed agent data
5. **Indexing**: Ensure proper database indexing on UIDs

## 🚨 Common Issues & Solutions

### Issue: Agent Not Found
```
Error: Agent agent-abc123 not found
Solution: Verify agent UID exists in database
```

### Issue: Permission Denied
```
Error: Agent lacks permission 'edit_community'
Solution: Check agent capabilities and assignment status
```

### Issue: Memory Expired
```
Error: Context memory has expired
Solution: Store fresh context or extend expiry time
```

## 📊 Agent Types Quick Reference

| Type | Capabilities | Use Case |
|------|-------------|----------|
| `COMMUNITY_LEADER` | Full permissions | Main community agent |
| `MODERATOR` | Moderation only | Content & user management |
| `ASSISTANT` | Basic functions | Support & help |

## 🔐 Standard Capabilities

- `edit_community` - Modify community settings
- `moderate_users` - Manage users and content
- `send_messages` - Send notifications
- `view_analytics` - Access metrics
- `manage_events` - Handle events
- `handle_reports` - Process reports

## 📱 Frontend Integration Examples

### React Hook Example
```javascript
const useAgent = (communityId) => {
  const [agent, setAgent] = useState(null);
  
  useEffect(() => {
    // GraphQL query to get community leader
    getCommunityLeader(communityId).then(setAgent);
  }, [communityId]);
  
  return agent;
};
```

### Vue.js Component Example
```javascript
export default {
  data() {
    return {
      agents: []
    }
  },
  async mounted() {
    this.agents = await this.$apollo.query({
      query: GET_COMMUNITY_AGENTS,
      variables: { community_uid: this.communityId }
    });
  }
}
```

This quick reference should help the development team get started quickly with the agentic system!