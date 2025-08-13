# Agentic Community Management API Documentation

## Overview

The Agentic Community Management system provides AI agents that can serve as community leaders, moderators, and assistants. This API allows you to create, manage, and interact with these agents through GraphQL operations.

## Table of Contents

1. [Authentication](#authentication)
2. [Agent Types](#agent-types)
3. [Capabilities and Permissions](#capabilities-and-permissions)
4. [GraphQL Mutations](#graphql-mutations)
5. [GraphQL Queries](#graphql-queries)
6. [Error Handling](#error-handling)
7. [Usage Examples](#usage-examples)
8. [Best Practices](#best-practices)

## Authentication

All API operations require authentication. The system uses JWT tokens for authentication.

```graphql
# Include JWT token in headers
Authorization: Bearer <your-jwt-token>
```

## Agent Types

The system supports three types of agents:

### COMMUNITY_LEADER
- **Purpose**: Primary leadership and management of communities
- **Default Capabilities**: `edit_community`, `moderate_users`, `manage_events`, `send_messages`
- **Restrictions**: Only one active leader per community (unless explicitly allowed)

### MODERATOR
- **Purpose**: Content moderation and user management
- **Default Capabilities**: `moderate_users`, `delete_content`, `send_messages`
- **Restrictions**: Multiple moderators allowed per community

### ASSISTANT
- **Purpose**: General assistance and communication
- **Default Capabilities**: `send_messages`, `fetch_metrics`
- **Restrictions**: Multiple assistants allowed per community

## Capabilities and Permissions

### Standard Capabilities

| Capability | Description | Agent Types |
|------------|-------------|-------------|
| `edit_community` | Modify community settings and information | COMMUNITY_LEADER |
| `moderate_users` | Warn, mute, or ban users | COMMUNITY_LEADER, MODERATOR |
| `manage_events` | Create and manage community events | COMMUNITY_LEADER |
| `send_messages` | Send messages and announcements | All types |
| `delete_content` | Remove inappropriate content | COMMUNITY_LEADER, MODERATOR |
| `fetch_metrics` | Access community analytics | All types |
| `view_reports` | View moderation and activity reports | COMMUNITY_LEADER, MODERATOR |
| `ban_users` | Permanently ban users from community | COMMUNITY_LEADER |

### Assignment-Specific Permissions

In addition to agent capabilities, assignments can have specific permissions:

- `manage_events`: Override for event management
- `access_admin_panel`: Special administrative access
- `bulk_operations`: Perform bulk user operations

## GraphQL Mutations

### createAgent

Create a new AI agent.

```graphql
mutation CreateAgent($input: CreateAgentInput!) {
  createAgent(input: $input) {
    success
    message
    agent {
      uid
      name
      agentType
      capabilities
      status
      createdDate
    }
    errors
  }
}
```

**Input Parameters:**
- `name` (String, required): Human-readable name for the agent
- `agentType` (String, required): Type of agent (COMMUNITY_LEADER, MODERATOR, ASSISTANT)
- `capabilities` (List[String], required): List of capabilities for the agent
- `description` (String, optional): Detailed description of the agent's purpose
- `iconId` (String, optional): Reference to agent's avatar/icon image
- `createdByUid` (String, optional): UID of user creating the agent

**Example:**
```graphql
{
  "input": {
    "name": "Community Helper Bot",
    "agentType": "COMMUNITY_LEADER",
    "capabilities": ["edit_community", "moderate_users", "send_messages"],
    "description": "An AI agent to help manage the community",
    "createdByUid": "user-123"
  }
}
```

### assignAgentToCommunity

Assign an agent to a community as a leader or moderator.

```graphql
mutation AssignAgentToCommunity($input: AssignAgentToCommunityInput!) {
  assignAgentToCommunity(input: $input) {
    success
    message
    assignment {
      uid
      status
      permissions
      assignmentDate
    }
    agent {
      uid
      name
    }
    community {
      uid
      name
    }
    errors
  }
}
```

**Input Parameters:**
- `agentUid` (String, required): UID of the agent to assign
- `communityUid` (String, required): UID of the community
- `assignedByUid` (String, required): UID of user making the assignment
- `permissions` (List[String], optional): Additional permissions for this assignment
- `allowMultipleLeaders` (Boolean, optional): Whether to allow multiple active leaders

**Example:**
```graphql
{
  "input": {
    "agentUid": "agent-456",
    "communityUid": "community-789",
    "assignedByUid": "user-123",
    "permissions": ["manage_events"],
    "allowMultipleLeaders": false
  }
}
```

### updateAgent

Update an existing agent's properties.

```graphql
mutation UpdateAgent($input: UpdateAgentInput!) {
  updateAgent(input: $input) {
    success
    message
    agent {
      uid
      name
      description
      capabilities
      status
    }
    errors
  }
}
```

**Input Parameters:**
- `agentUid` (String, required): UID of the agent to update
- `name` (String, optional): New name for the agent
- `description` (String, optional): New description
- `capabilities` (List[String], optional): New capabilities list
- `status` (String, optional): New status (ACTIVE, INACTIVE, SUSPENDED)
- `iconId` (String, optional): New icon reference

### deactivateAgentAssignment

Remove an agent's assignment from a community.

```graphql
mutation DeactivateAgentAssignment($input: DeactivateAgentAssignmentInput!) {
  deactivateAgentAssignment(input: $input) {
    success
    message
    assignment {
      uid
      status
      isActive
    }
    successFlag
    errors
  }
}
```

**Input Parameters:**
- `assignmentUid` (String, required): UID of the assignment to deactivate
- `reason` (String, optional): Reason for deactivation

### storeAgentContext

Store context information for an agent.

```graphql
mutation StoreAgentContext($input: StoreAgentContextInput!) {
  storeAgentContext(input: $input) {
    success
    message
    errors
  }
}
```

**Input Parameters:**
- `agentUid` (String, required): UID of the agent
- `communityUid` (String, required): UID of the community
- `context` (JSONString, required): Context data to store
- `expiresInHours` (Int, optional): Expiration time in hours
- `priority` (Int, optional): Priority for memory cleanup

## GraphQL Queries

### getAgent

Retrieve a specific agent by UID.

```graphql
query GetAgent($agentUid: String!) {
  getAgent(agentUid: $agentUid) {
    uid
    name
    description
    agentType
    capabilities
    status
    isActive
    assignmentCount
    createdDate
    updatedDate
    assignments {
      uid
      status
      permissions
      community {
        uid
        name
      }
    }
    createdBy {
      uid
      username
    }
  }
}
```

### getAgents

Retrieve a list of agents with optional filtering and pagination.

```graphql
query GetAgents($filters: AgentFilterInput, $pagination: PaginationInput) {
  getAgents(filters: $filters, pagination: $pagination) {
    uid
    name
    agentType
    capabilities
    status
    isActive
    assignmentCount
    createdDate
  }
}
```

**Filter Options:**
- `agentType`: Filter by agent type
- `status`: Filter by agent status
- `hasCapability`: Filter agents with specific capability
- `createdAfter`: Filter by creation date
- `nameContains`: Filter by name substring

**Pagination Options:**
- `page`: Page number (1-based)
- `pageSize`: Number of items per page
- `orderBy`: Field to order by
- `orderDirection`: Order direction (ASC or DESC)

### getCommunityLeader

Get the current leader agent for a community.

```graphql
query GetCommunityLeader($communityUid: String!) {
  getCommunityLeader(communityUid: $communityUid) {
    uid
    name
    agentType
    capabilities
    isActive
    assignments {
      uid
      status
      permissions
      assignmentDate
    }
  }
}
```

### getAgentAssignments

Get all assignments for a specific agent.

```graphql
query GetAgentAssignments($agentUid: String!) {
  getAgentAssignments(agentUid: $agentUid) {
    uid
    status
    permissions
    assignmentDate
    isActive
    agent {
      uid
      name
    }
    community {
      uid
      name
    }
    assignedBy {
      uid
      username
    }
  }
}
```

### getAgentPermissions

Check what permissions an agent has in a specific community.

```graphql
query GetAgentPermissions($agentUid: String!, $communityUid: String!) {
  getAgentPermissions(agentUid: $agentUid, communityUid: $communityUid)
}
```

### validateAgentPermission

Check if an agent has a specific permission in a community.

```graphql
query ValidateAgentPermission($agentUid: String!, $communityUid: String!, $permission: String!) {
  validateAgentPermission(agentUid: $agentUid, communityUid: $communityUid, permission: $permission)
}
```

## Error Handling

The API uses structured error responses with specific error codes:

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `AGENT_NOT_FOUND` | Agent with specified UID not found | 404 |
| `COMMUNITY_NOT_FOUND` | Community with specified UID not found | 404 |
| `USER_NOT_FOUND` | User with specified UID not found | 404 |
| `AGENT_AUTHENTICATION_FAILED` | Agent authentication failed | 401 |
| `AGENT_AUTHORIZATION_FAILED` | Agent lacks required permissions | 403 |
| `AGENT_VALIDATION_ERROR` | Invalid agent data provided | 400 |
| `COMMUNITY_ALREADY_HAS_LEADER` | Community already has an active leader | 409 |
| `AGENT_ALREADY_ASSIGNED` | Agent is already assigned to the community | 409 |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "error_type": "AgentNotFoundError",
    "error_code": "AGENT_NOT_FOUND",
    "message": "Agent not found: agent-123",
    "details": {
      "agent_uid": "agent-123"
    }
  },
  "message": "Agent not found: agent-123",
  "errors": ["Agent not found: agent-123"]
}
```

## Usage Examples

### Complete Agent Setup Workflow

```javascript
// 1. Create an agent
const createAgentMutation = `
  mutation CreateAgent($input: CreateAgentInput!) {
    createAgent(input: $input) {
      success
      message
      agent {
        uid
        name
        agentType
        capabilities
      }
      errors
    }
  }
`;

const createAgentResult = await graphqlClient.request(createAgentMutation, {
  input: {
    name: "Community Manager AI",
    agentType: "COMMUNITY_LEADER",
    capabilities: ["edit_community", "moderate_users", "send_messages"],
    description: "AI agent to manage community activities",
    createdByUid: "user-123"
  }
});

if (!createAgentResult.createAgent.success) {
  console.error("Failed to create agent:", createAgentResult.createAgent.errors);
  return;
}

const agentUid = createAgentResult.createAgent.agent.uid;

// 2. Assign agent to community
const assignAgentMutation = `
  mutation AssignAgentToCommunity($input: AssignAgentToCommunityInput!) {
    assignAgentToCommunity(input: $input) {
      success
      message
      assignment {
        uid
        status
      }
      errors
    }
  }
`;

const assignResult = await graphqlClient.request(assignAgentMutation, {
  input: {
    agentUid: agentUid,
    communityUid: "community-456",
    assignedByUid: "user-123",
    permissions: ["manage_events"]
  }
});

if (!assignResult.assignAgentToCommunity.success) {
  console.error("Failed to assign agent:", assignResult.assignAgentToCommunity.errors);
  return;
}

console.log("Agent successfully created and assigned!");
```

### Checking Agent Permissions

```javascript
const checkPermissionQuery = `
  query ValidateAgentPermission($agentUid: String!, $communityUid: String!, $permission: String!) {
    validateAgentPermission(agentUid: $agentUid, communityUid: $communityUid, permission: $permission)
  }
`;

const hasPermission = await graphqlClient.request(checkPermissionQuery, {
  agentUid: "agent-789",
  communityUid: "community-456",
  permission: "moderate_users"
});

if (hasPermission.validateAgentPermission) {
  console.log("Agent has moderation permissions");
  // Proceed with moderation action
} else {
  console.log("Agent lacks moderation permissions");
  // Handle permission denied
}
```

### Storing Agent Context

```javascript
const storeContextMutation = `
  mutation StoreAgentContext($input: StoreAgentContextInput!) {
    storeAgentContext(input: $input) {
      success
      message
      errors
    }
  }
`;

const contextData = {
  currentTask: "community_onboarding",
  progress: 75,
  lastAction: "sent_welcome_message",
  pendingActions: ["setup_rules", "create_channels"]
};

const storeResult = await graphqlClient.request(storeContextMutation, {
  input: {
    agentUid: "agent-789",
    communityUid: "community-456",
    context: JSON.stringify(contextData),
    expiresInHours: 24,
    priority: 1
  }
});

if (storeResult.storeAgentContext.success) {
  console.log("Agent context stored successfully");
}
```

### Retrieving Community Information

```javascript
const getCommunityInfoQuery = `
  query GetCommunityInfo($communityUid: String!) {
    getCommunityLeader(communityUid: $communityUid) {
      uid
      name
      agentType
      capabilities
      isActive
    }
    getCommunityAgents(communityUid: $communityUid) {
      agent {
        uid
        name
        agentType
      }
      assignment {
        status
        permissions
      }
      isLeader
    }
  }
`;

const communityInfo = await graphqlClient.request(getCommunityInfoQuery, {
  communityUid: "community-456"
});

console.log("Community Leader:", communityInfo.getCommunityLeader);
console.log("All Agents:", communityInfo.getCommunityAgents);
```

### Error Handling Example

```javascript
async function createAgentWithErrorHandling(agentData) {
  try {
    const result = await graphqlClient.request(createAgentMutation, {
      input: agentData
    });
    
    if (!result.createAgent.success) {
      // Handle business logic errors
      const errors = result.createAgent.errors;
      console.error("Agent creation failed:", errors);
      
      // Check for specific error types
      if (errors.some(error => error.includes("AGENT_VALIDATION_ERROR"))) {
        console.log("Please check agent data format");
      } else if (errors.some(error => error.includes("USER_NOT_FOUND"))) {
        console.log("Creator user not found");
      }
      
      return null;
    }
    
    return result.createAgent.agent;
    
  } catch (error) {
    // Handle network or GraphQL syntax errors
    console.error("Request failed:", error);
    return null;
  }
}
```

## Best Practices

### 1. Agent Lifecycle Management

- **Create agents with specific purposes**: Don't create generic agents; define clear roles and capabilities
- **Use appropriate agent types**: Choose COMMUNITY_LEADER for management, MODERATOR for content control, ASSISTANT for general help
- **Regularly review agent assignments**: Deactivate unused assignments to maintain security

### 2. Permission Management

- **Follow principle of least privilege**: Only grant necessary capabilities and permissions
- **Use assignment-specific permissions**: Add extra permissions at assignment level rather than modifying agent capabilities
- **Regularly audit permissions**: Use the audit logging system to track permission usage

### 3. Memory and Context

- **Set appropriate expiration times**: Don't store context indefinitely; use reasonable expiration periods
- **Use priority levels**: Set higher priority for critical context data
- **Clean up regularly**: Implement regular cleanup of expired memory

### 4. Error Handling

- **Always check success flags**: Don't assume operations succeeded
- **Handle specific error codes**: Implement different handling for different error types
- **Log errors appropriately**: Use structured logging for debugging

### 5. Performance Considerations

- **Use pagination**: Always paginate large result sets
- **Filter queries**: Use filters to reduce data transfer
- **Batch operations**: Use bulk operations when available
- **Cache frequently accessed data**: Cache agent permissions and assignments

### 6. Security

- **Validate all inputs**: Never trust client-side validation alone
- **Use authentication**: Always require valid JWT tokens
- **Audit all operations**: Enable comprehensive audit logging
- **Regular security reviews**: Periodically review agent permissions and assignments

### 7. Monitoring and Maintenance

- **Monitor agent activity**: Track agent actions and performance
- **Set up alerts**: Alert on failed operations or suspicious activity
- **Regular backups**: Backup agent configurations and memory data
- **Update documentation**: Keep API documentation current with changes

## Rate Limits

The API implements rate limiting to prevent abuse:

- **Agent creation**: 10 agents per hour per user
- **Assignment operations**: 50 assignments per hour per user
- **Memory operations**: 1000 operations per hour per agent
- **Query operations**: 10000 queries per hour per user

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when rate limit resets

## Webhooks

The system supports webhooks for real-time notifications:

### Supported Events

- `agent.assigned`: Agent assigned to community
- `agent.deactivated`: Agent assignment deactivated
- `agent.action`: Agent performed an action
- `community.updated`: Community updated by agent
- `user.moderated`: User moderated by agent

### Webhook Configuration

Configure webhooks in your application settings or through the management API.

### Webhook Payload Example

```json
{
  "event_type": "agent.assigned",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "agent_uid": "agent-123",
    "community_uid": "community-456",
    "assignment_uid": "assignment-789",
    "assigned_by_uid": "user-123"
  }
}
```

## Support and Resources

- **API Status**: Check system status at `/health`
- **GraphQL Playground**: Interactive API explorer at `/graphql`
- **Documentation**: Latest docs at `/docs`
- **Support**: Contact support for technical issues
- **Community**: Join our developer community for discussions