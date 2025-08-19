# Agentic Community Management API Documentation

## Overview
The Agentic Community Management System provides a comprehensive GraphQL API for managing AI agents within communities. This system enables automatic agent assignment, permission management, memory persistence, and community moderation.

## GraphQL Endpoint
```
POST /graphql
```

## Authentication
Most mutations require authentication. Use JWT tokens in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

---

## 🤖 Agent Management APIs

### 1. Create Agent
Creates a new AI agent with specified capabilities.

**Mutation:**
```graphql
mutation CreateAgent($input: CreateAgentInput!) {
  create_agent(input: $input) {
    success
    message
    errors
    agent {
      uid
      name
      agent_type
      capabilities
      status
      description
      created_date
    }
  }
}
```

**Input:**
```graphql
{
  "input": {
    "name": "Community Helper Bot",
    "agent_type": "COMMUNITY_LEADER",
    "capabilities": ["edit_community", "moderate_users", "send_messages"],
    "description": "AI assistant for community management",
    "created_by_uid": "user-123"
  }
}
```

### 2. Update Agent
Updates an existing agent's properties.

**Mutation:**
```graphql
mutation UpdateAgent($input: UpdateAgentInput!) {
  update_agent(input: $input) {
    success
    message
    errors
    agent {
      uid
      name
      description
      capabilities
      status
    }
  }
}
```

### 3. Get Agent by UID
Retrieves a specific agent by its unique identifier.

**Query:**
```graphql
query GetAgent($uid: String!) {
  get_agent(uid: $uid) {
    uid
    name
    agent_type
    capabilities
    status
    description
    created_date
    updated_date
  }
}
```

### 4. Get All Agents
Retrieves a list of all agents with optional filtering.

**Query:**
```graphql
query GetAgents($filter: AgentFilterInput, $pagination: PaginationInput) {
  get_agents(filter: $filter, pagination: $pagination) {
    uid
    name
    agent_type
    capabilities
    status
    description
  }
}
```

---

## 🏘️ Community Assignment APIs

### 1. Assign Agent to Community
Assigns an agent to a specific community with a defined role.

**Mutation:**
```graphql
mutation AssignAgentToCommunity($input: AssignAgentToCommunityInput!) {
  assign_agent_to_community(input: $input) {
    success
    message
    errors
    assignment {
      uid
      agent_uid
      community_uid
      role
      status
      assigned_date
    }
  }
}
```

**Input:**
```graphql
{
  "input": {
    "agent_uid": "agent-123",
    "community_uid": "community-456",
    "role": "LEADER",
    "assigned_by_uid": "user-789"
  }
}
```

### 2. Get Community Leader
Retrieves the current leader agent for a community.

**Query:**
```graphql
query GetCommunityLeader($community_uid: String!) {
  get_community_leader(community_uid: $community_uid) {
    uid
    name
    agent_type
    capabilities
    status
  }
}
```

### 3. Get Community Agents
Lists all agents assigned to a specific community.

**Query:**
```graphql
query GetCommunityAgents($community_uid: String!) {
  get_community_agents(community_uid: $community_uid) {
    uid
    name
    agent_type
    role
    status
    assigned_date
  }
}
```

### 4. Get Agent Assignments
Lists all community assignments for a specific agent.

**Query:**
```graphql
query GetAgentAssignments($agent_uid: String!) {
  get_agent_assignments(agent_uid: $agent_uid) {
    uid
    community_uid
    role
    status
    assigned_date
    permissions
  }
}
```

### 5. Update Agent Assignment
Updates an existing agent-community assignment.

**Mutation:**
```graphql
mutation UpdateAgentAssignment($input: UpdateAgentAssignmentInput!) {
  update_agent_assignment(input: $input) {
    success
    message
    errors
    assignment {
      uid
      role
      status
      permissions
    }
  }
}
```

### 6. Deactivate Agent Assignment
Removes an agent from a community.

**Mutation:**
```graphql
mutation DeactivateAgentAssignment($input: DeactivateAgentAssignmentInput!) {
  deactivate_agent_assignment(input: $input) {
    success
    message
    errors
  }
}
```

---

## 🧠 Agent Memory Management APIs

### 1. Store Agent Context
Stores contextual information for an agent in a specific community.

**Mutation:**
```graphql
mutation StoreAgentContext($input: StoreAgentContextInput!) {
  store_agent_context(input: $input) {
    success
    message
    errors
    memory {
      uid
      agent_uid
      community_uid
      memory_type
      content
      created_date
    }
  }
}
```

**Input:**
```graphql
{
  "input": {
    "agent_uid": "",
    "community_uid": "",
    "context_data": {
      "interaction_count": 15,
      "last_topics": ["community rules", "event planning"]
    },
    "context_type": "INTERACTION"
  }
}
```

### 2. Update Conversation History
Updates the conversation history for an agent.

**Mutation:**
```graphql
mutation UpdateConversationHistory($input: UpdateConversationHistoryInput!) {
  update_conversation_history(input: $input) {
    success
    message
    errors
    memory {
      uid
      content
      updated_date
    }
  }
}
```

### 3. Store Agent Knowledge
Stores knowledge base information for an agent.

**Mutation:**
```graphql
mutation StoreAgentKnowledge($input: StoreAgentKnowledgeInput!) {
  store_agent_knowledge(input: $input) {
    success
    message
    errors
    memory {
      uid
      content
      created_date
    }
  }
}
```

### 4. Store Agent Preferences
Stores user preferences and settings for an agent.

**Mutation:**
```graphql
mutation StoreAgentPreferences($input: StoreAgentPreferencesInput!) {
  store_agent_preferences(input: $input) {
    success
    message
    errors
    memory {
      uid
      content
      created_date
    }
  }
}
```

### 5. Get Conversation History
Retrieves conversation history for an agent in a community.

**Query:**
```graphql
query GetConversationHistory($input: GetConversationHistoryInput!) {
  get_conversation_history(input: $input) {
    success
    message
    history
  }
}
```

### 6. Get Community Knowledge
Retrieves knowledge base for an agent in a community.

**Query:**
```graphql
query GetCommunityKnowledge($input: GetCommunityKnowledgeInput!) {
  get_community_knowledge(input: $input) {
    success
    message
    knowledge
  }
}
```

### 7. Get Agent Preferences
Retrieves stored preferences for an agent.

**Query:**
```graphql
query GetAgentPreferences($input: GetAgentPreferencesInput!) {
  get_agent_preferences(input: $input) {
    success
    message
    preferences
  }
}
```

### 8. Clear Agent Memory
Clears specific types of memory for an agent.

**Mutation:**
```graphql
mutation ClearAgentMemory($input: ClearAgentMemoryInput!) {
  clear_agent_memory(input: $input) {
    success
    message
    errors
    cleared_count
  }
}
```

### 9. Get Memory Statistics
Retrieves memory usage statistics for an agent.

**Query:**
```graphql
query GetMemoryStats($input: GetMemoryStatsInput!) {
  get_memory_stats(input: $input) {
    success
    message
    stats
  }
}
```

---

## 🔐 Authentication & Authorization APIs

### 1. Log Agent Action
Records an action performed by an agent for audit purposes.

**Mutation:**
```graphql
mutation LogAgentAction($input: LogAgentActionInput!) {
  log_agent_action(input: $input) {
    success
    message
    errors
    action_log {
      uid
      agent_uid
      action_type
      result
      timestamp
    }
  }
}
```

### 2. Get Agent Action History
Retrieves the action history for an agent.

**Query:**
```graphql
query GetAgentActionHistory($input: GetAgentActionHistoryInput!) {
  get_agent_action_history(input: $input) {
    success
    message
    history
  }
}
```

### 3. Validate Agent Action
Validates if an agent has permission to perform a specific action.

**Query:**
```graphql
query ValidateAgentAction($input: ValidateAgentActionInput!) {
  validate_agent_action(input: $input) {
    success
    message
    allowed
    reason
  }
}
```

### 4. Generate Audit Report
Generates a comprehensive audit report for an agent.

**Query:**
```graphql
query GenerateAuditReport($input: GenerateAuditReportInput!) {
  generate_audit_report(input: $input) {
    success
    message
    report
  }
}
```

---

## 🔧 Advanced Management APIs

### 1. Manage Agent Capabilities
Add or remove capabilities from an agent.

**Mutation:**
```graphql
mutation ManageAgentCapabilities($input: AgentCapabilityInput!) {
  manage_agent_capabilities(input: $input) {
    success
    message
    errors
    agent {
      uid
      capabilities
    }
  }
}
```

### 2. Manage Assignment Permissions
Manage permissions for a specific agent assignment.

**Mutation:**
```graphql
mutation ManageAssignmentPermissions($input: AgentPermissionInput!) {
  manage_assignment_permissions(input: $input) {
    success
    message
    errors
    assignment {
      uid
      permissions
    }
  }
}
```

### 3. Bulk Agent Operations
Perform bulk operations on multiple agents.

**Mutation:**
```graphql
mutation BulkAgentOperation($input: BulkAgentOperationInput!) {
  bulk_agent_operation(input: $input) {
    success
    message
    errors
    affected_count
    results
  }
}
```

### 4. Bulk Assignment Operations
Perform bulk operations on multiple assignments.

**Mutation:**
```graphql
mutation BulkAssignmentOperation($input: BulkAssignmentOperationInput!) {
  bulk_assignment_operation(input: $input) {
    success
    message
    errors
    affected_count
    results
  }
}
```

### 5. Cleanup Expired Memory
Clean up expired memory records.

**Mutation:**
```graphql
mutation CleanupExpiredMemory {
  cleanup_expired_memory {
    success
    message
    errors
    cleared_count
  }
}
```

---

## 📊 Agent Types and Capabilities

### Agent Types
- `COMMUNITY_LEADER`: Full community management permissions
- `MODERATOR`: User moderation and content management
- `ASSISTANT`: Basic interaction and support functions

### Standard Capabilities
- `edit_community`: Modify community settings and information
- `moderate_users`: Manage user permissions and behavior
- `send_messages`: Send messages and notifications
- `view_analytics`: Access community metrics and reports
- `manage_events`: Create and manage community events
- `handle_reports`: Process user reports and complaints

### Assignment Roles
- `LEADER`: Primary agent for the community
- `MODERATOR`: Secondary moderation agent
- `ASSISTANT`: Support and helper agent

### Memory Types
- `CONTEXT`: General contextual information
- `CONVERSATION`: Chat and interaction history
- `KNOWLEDGE`: Community-specific knowledge base
- `PREFERENCES`: User preferences and settings

---

## 🚨 Error Handling

All mutations return a standardized response format:

```graphql
{
  "success": boolean,
  "message": "Human-readable message",
  "errors": ["List of error messages"],
  "data": { /* Relevant data object */ }
}
```

### Common Error Codes
- `AGENT_NOT_FOUND`: Agent with specified UID doesn't exist
- `COMMUNITY_NOT_FOUND`: Community with specified UID doesn't exist
- `PERMISSION_DENIED`: Agent lacks required permissions
- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_REQUIRED`: User authentication required
- `ASSIGNMENT_EXISTS`: Agent already assigned to community
- `MEMORY_EXPIRED`: Requested memory has expired

---

## 📝 Usage Examples

### Complete Agent Setup Flow
```graphql
# 1. Create an agent
mutation {
  create_agent(input: {
    name: "Community Helper",
    agent_type: "COMMUNITY_LEADER",
    capabilities: ["edit_community", "moderate_users"],
    description: "Main community management agent",
    created_by_uid: "admin-123"
  }) {
    success
    agent { uid }
  }
}

# 2. Assign to community
mutation {
  assign_agent_to_community(input: {
    agent_uid: "agent-456",
    community_uid: "community-789",
    role: "LEADER",
    assigned_by_uid: "admin-123"
  }) {
    success
    assignment { uid }
  }
}

# 3. Store initial context
mutation {
  store_agent_context(input: {
    agent_uid: "agent-456",
    community_uid: "community-789",
    context_data: {
      "setup_complete": true,
      "initial_greeting": "Hello! I'm your community assistant."
    },
    context_type: "CONTEXT"
  }) {
    success
  }
}
```

---

## 🔗 Integration Notes

1. **Frontend Integration**: Use these APIs to build agent management interfaces
2. **Webhook Support**: Agent events trigger webhooks for external integrations
3. **Real-time Updates**: Subscribe to agent status changes via WebSocket
4. **Batch Operations**: Use bulk operations for efficient mass management
5. **Memory Management**: Implement memory cleanup strategies for optimal performance


