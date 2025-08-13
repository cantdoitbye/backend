# Agentic Community Management - Usage Examples

This document provides practical examples of how to use the Agentic Community Management system in various scenarios.

## Table of Contents

1. [Basic Agent Setup](#basic-agent-setup)
2. [Community Leadership Scenarios](#community-leadership-scenarios)
3. [Moderation Workflows](#moderation-workflows)
4. [Memory and Context Management](#memory-and-context-management)
5. [Permission Management](#permission-management)
6. [Bulk Operations](#bulk-operations)
7. [Integration Examples](#integration-examples)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Basic Agent Setup

### Creating Your First Agent

```javascript
// Example: Creating a community leader agent
const createCommunityLeader = async () => {
  const mutation = `
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
  `;

  const variables = {
    input: {
      name: "Community Helper AI",
      agentType: "COMMUNITY_LEADER",
      capabilities: [
        "edit_community",
        "moderate_users", 
        "manage_events",
        "send_messages"
      ],
      description: "An AI assistant to help manage and grow our community",
      createdByUid: "user-12345"
    }
  };

  try {
    const result = await graphqlClient.request(mutation, variables);
    
    if (result.createAgent.success) {
      console.log("✅ Agent created successfully!");
      console.log("Agent UID:", result.createAgent.agent.uid);
      return result.createAgent.agent;
    } else {
      console.error("❌ Failed to create agent:", result.createAgent.errors);
      return null;
    }
  } catch (error) {
    console.error("❌ Request failed:", error);
    return null;
  }
};
```

### Assigning Agent to Community

```javascript
// Example: Assigning the agent to manage a community
const assignAgentToManageCommunity = async (agentUid, communityUid, assignerUid) => {
  const mutation = `
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
  `;

  const variables = {
    input: {
      agentUid: agentUid,
      communityUid: communityUid,
      assignedByUid: assignerUid,
      permissions: ["manage_events", "access_analytics"],
      allowMultipleLeaders: false
    }
  };

  try {
    const result = await graphqlClient.request(mutation, variables);
    
    if (result.assignAgentToCommunity.success) {
      console.log("✅ Agent assigned successfully!");
      console.log(`Agent "${result.assignAgentToCommunity.agent.name}" is now managing "${result.assignAgentToCommunity.community.name}"`);
      return result.assignAgentToCommunity.assignment;
    } else {
      console.error("❌ Failed to assign agent:", result.assignAgentToCommunity.errors);
      return null;
    }
  } catch (error) {
    console.error("❌ Assignment failed:", error);
    return null;
  }
};
```

## Community Leadership Scenarios

### Scenario 1: New Community Setup

```javascript
// Complete workflow for setting up a new community with an AI leader
const setupNewCommunityWithAI = async (communityData, creatorUid) => {
  console.log("🚀 Starting new community setup with AI leader...");

  // Step 1: Create the community (assuming this exists)
  const community = await createCommunity(communityData);
  if (!community) {
    console.error("❌ Failed to create community");
    return null;
  }

  // Step 2: Create a specialized leader agent for this community
  const agentData = {
    name: `${communityData.name} AI Leader`,
    agentType: "COMMUNITY_LEADER",
    capabilities: [
      "edit_community",
      "moderate_users",
      "manage_events",
      "send_messages",
      "view_reports"
    ],
    description: `AI leader specifically created for ${communityData.name} community`,
    createdByUid: creatorUid
  };

  const agent = await createCommunityLeader(agentData);
  if (!agent) {
    console.error("❌ Failed to create agent");
    return null;
  }

  // Step 3: Assign agent to community
  const assignment = await assignAgentToManageCommunity(
    agent.uid, 
    community.uid, 
    creatorUid
  );
  if (!assignment) {
    console.error("❌ Failed to assign agent");
    return null;
  }

  // Step 4: Initialize agent context with community setup tasks
  const initialContext = {
    setupPhase: "initialization",
    tasks: [
      "welcome_new_members",
      "establish_community_rules",
      "create_introduction_channel",
      "schedule_first_event"
    ],
    communityGoals: communityData.goals || [],
    setupProgress: 0
  };

  await storeAgentContext(agent.uid, community.uid, initialContext);

  console.log("✅ Community setup complete!");
  console.log(`🤖 AI Leader "${agent.name}" is now managing "${community.name}"`);

  return {
    community,
    agent,
    assignment
  };
};
```

### Scenario 2: Agent Handover

```javascript
// Transferring community leadership from one agent to another
const transferCommunityLeadership = async (
  oldAgentUid, 
  newAgentUid, 
  communityUid, 
  transferredByUid
) => {
  console.log("🔄 Starting leadership transfer...");

  try {
    // Step 1: Get current assignment
    const currentAssignments = await getAgentAssignments(oldAgentUid);
    const currentAssignment = currentAssignments.find(
      a => a.community.uid === communityUid && a.isActive
    );

    if (!currentAssignment) {
      console.error("❌ No active assignment found for current agent");
      return false;
    }

    // Step 2: Transfer context and memory from old agent to new agent
    const oldContext = await getAgentContext(oldAgentUid, communityUid);
    const conversationHistory = await getConversationHistory(oldAgentUid, communityUid);
    const communityKnowledge = await getCommunityKnowledge(oldAgentUid, communityUid);

    // Step 3: Store transferred knowledge in new agent
    if (oldContext && Object.keys(oldContext).length > 0) {
      const transferContext = {
        ...oldContext,
        transferredFrom: oldAgentUid,
        transferDate: new Date().toISOString(),
        transferReason: "leadership_handover"
      };
      await storeAgentContext(newAgentUid, communityUid, transferContext);
    }

    if (communityKnowledge && Object.keys(communityKnowledge).length > 0) {
      await storeAgentKnowledge(newAgentUid, communityUid, communityKnowledge);
    }

    // Step 4: Deactivate old assignment
    const deactivateResult = await deactivateAgentAssignment(
      currentAssignment.uid,
      "Leadership transferred to new agent"
    );

    if (!deactivateResult.success) {
      console.error("❌ Failed to deactivate old assignment");
      return false;
    }

    // Step 5: Assign new agent
    const newAssignment = await assignAgentToManageCommunity(
      newAgentUid,
      communityUid,
      transferredByUid
    );

    if (!newAssignment) {
      console.error("❌ Failed to assign new agent");
      return false;
    }

    console.log("✅ Leadership transfer completed successfully!");
    return true;

  } catch (error) {
    console.error("❌ Leadership transfer failed:", error);
    return false;
  }
};
```

## Moderation Workflows

### Scenario 1: Automated Content Moderation

```javascript
// Example of an agent performing automated moderation
const performAutomatedModeration = async (agentUid, communityUid, contentReport) => {
  console.log("🛡️ Starting automated moderation...");

  // Step 1: Check if agent has moderation permissions
  const hasPermission = await validateAgentPermission(
    agentUid, 
    communityUid, 
    "moderate_users"
  );

  if (!hasPermission) {
    console.error("❌ Agent lacks moderation permissions");
    return null;
  }

  // Step 2: Analyze the content report
  const moderationDecision = analyzeModerationReport(contentReport);

  // Step 3: Take appropriate action based on severity
  let actionTaken = null;

  switch (moderationDecision.severity) {
    case "low":
      // Just log the incident
      actionTaken = await logModerationIncident(agentUid, communityUid, {
        type: "content_flagged",
        severity: "low",
        contentId: contentReport.contentId,
        reason: moderationDecision.reason,
        action: "logged_only"
      });
      break;

    case "medium":
      // Warn the user and remove content
      actionTaken = await moderateUser(agentUid, communityUid, {
        targetUserId: contentReport.userId,
        action: "warn",
        reason: moderationDecision.reason,
        removeContent: true,
        contentId: contentReport.contentId
      });
      break;

    case "high":
      // Temporarily mute the user
      actionTaken = await moderateUser(agentUid, communityUid, {
        targetUserId: contentReport.userId,
        action: "mute",
        duration: "24h",
        reason: moderationDecision.reason,
        removeContent: true,
        contentId: contentReport.contentId
      });
      break;

    case "critical":
      // Ban the user and escalate to human moderators
      actionTaken = await moderateUser(agentUid, communityUid, {
        targetUserId: contentReport.userId,
        action: "ban",
        reason: moderationDecision.reason,
        removeContent: true,
        contentId: contentReport.contentId,
        escalateToHuman: true
      });
      break;
  }

  // Step 4: Update agent context with moderation activity
  const currentContext = await getAgentContext(agentUid, communityUid);
  const updatedContext = {
    ...currentContext,
    lastModerationAction: {
      timestamp: new Date().toISOString(),
      severity: moderationDecision.severity,
      action: actionTaken?.action,
      contentId: contentReport.contentId,
      userId: contentReport.userId
    },
    moderationStats: {
      ...currentContext.moderationStats,
      totalActions: (currentContext.moderationStats?.totalActions || 0) + 1,
      [moderationDecision.severity]: (currentContext.moderationStats?.[moderationDecision.severity] || 0) + 1
    }
  };

  await storeAgentContext(agentUid, communityUid, updatedContext);

  console.log(`✅ Moderation completed: ${moderationDecision.severity} severity, action: ${actionTaken?.action}`);
  return actionTaken;
};

// Helper function to analyze moderation reports
const analyzeModerationReport = (report) => {
  // This would typically use AI/ML models to analyze content
  // For this example, we'll use simple rule-based logic
  
  const keywords = {
    critical: ["hate speech", "threats", "doxxing"],
    high: ["harassment", "spam", "inappropriate"],
    medium: ["off-topic", "rude", "argumentative"],
    low: ["minor violation", "borderline"]
  };

  for (const [severity, terms] of Object.entries(keywords)) {
    if (terms.some(term => report.reason.toLowerCase().includes(term))) {
      return {
        severity,
        reason: report.reason,
        confidence: 0.8 // Would be calculated by AI model
      };
    }
  }

  return {
    severity: "low",
    reason: report.reason,
    confidence: 0.5
  };
};
```

### Scenario 2: Escalation to Human Moderators

```javascript
// Example of agent escalating complex cases to human moderators
const escalateToHumanModerator = async (agentUid, communityUid, escalationData) => {
  console.log("🚨 Escalating to human moderator...");

  // Step 1: Create escalation record
  const escalation = {
    agentUid,
    communityUid,
    escalationType: escalationData.type,
    severity: escalationData.severity,
    description: escalationData.description,
    evidence: escalationData.evidence,
    timestamp: new Date().toISOString(),
    status: "pending_human_review"
  };

  // Step 2: Store escalation in agent memory for tracking
  const currentContext = await getAgentContext(agentUid, communityUid);
  const updatedContext = {
    ...currentContext,
    pendingEscalations: [
      ...(currentContext.pendingEscalations || []),
      escalation
    ],
    escalationStats: {
      ...currentContext.escalationStats,
      total: (currentContext.escalationStats?.total || 0) + 1,
      pending: (currentContext.escalationStats?.pending || 0) + 1
    }
  };

  await storeAgentContext(agentUid, communityUid, updatedContext);

  // Step 3: Notify human moderators (this would integrate with your notification system)
  await notifyHumanModerators(communityUid, escalation);

  // Step 4: Log the escalation action
  await logAgentAction(agentUid, communityUid, {
    actionType: "escalate_to_human",
    details: escalation,
    success: true
  });

  console.log("✅ Escalation created and human moderators notified");
  return escalation;
};
```

## Memory and Context Management

### Scenario 1: Conversation Context Tracking

```javascript
// Example of maintaining conversation context across interactions
const handleUserInteraction = async (agentUid, communityUid, userMessage) => {
  console.log("💬 Processing user interaction...");

  // Step 1: Retrieve current conversation context
  const conversationHistory = await getConversationHistory(agentUid, communityUid, 10);
  const currentContext = await getAgentContext(agentUid, communityUid);

  // Step 2: Process the user message with context
  const response = await generateAgentResponse(userMessage, {
    conversationHistory,
    currentContext,
    communityInfo: await getCommunityInfo(communityUid)
  });

  // Step 3: Update conversation history
  const conversationEntry = {
    timestamp: new Date().toISOString(),
    user: userMessage.userId,
    message: userMessage.content,
    agentResponse: response.content,
    intent: response.detectedIntent,
    confidence: response.confidence
  };

  await updateConversationHistory(agentUid, communityUid, conversationEntry);

  // Step 4: Update agent context based on interaction
  const updatedContext = {
    ...currentContext,
    lastInteraction: {
      timestamp: new Date().toISOString(),
      userId: userMessage.userId,
      intent: response.detectedIntent,
      resolved: response.resolved
    },
    interactionStats: {
      ...currentContext.interactionStats,
      total: (currentContext.interactionStats?.total || 0) + 1,
      [response.detectedIntent]: (currentContext.interactionStats?.[response.detectedIntent] || 0) + 1
    }
  };

  // Step 5: Handle specific intents
  if (response.detectedIntent === "community_question") {
    updatedContext.pendingQuestions = [
      ...(currentContext.pendingQuestions || []),
      {
        userId: userMessage.userId,
        question: userMessage.content,
        timestamp: new Date().toISOString(),
        status: "answered"
      }
    ];
  }

  await storeAgentContext(agentUid, communityUid, updatedContext);

  console.log("✅ User interaction processed and context updated");
  return response;
};
```

### Scenario 2: Learning from Community Patterns

```javascript
// Example of agent learning and adapting to community patterns
const updateCommunityKnowledge = async (agentUid, communityUid, learningData) => {
  console.log("🧠 Updating community knowledge...");

  // Step 1: Get existing community knowledge
  const existingKnowledge = await getCommunityKnowledge(agentUid, communityUid);

  // Step 2: Analyze new patterns
  const patterns = analyzeCommunityPatterns(learningData);

  // Step 3: Update knowledge base
  const updatedKnowledge = {
    ...existingKnowledge,
    patterns: {
      ...existingKnowledge.patterns,
      ...patterns
    },
    lastUpdated: new Date().toISOString(),
    learningCycles: (existingKnowledge.learningCycles || 0) + 1
  };

  // Step 4: Store updated knowledge
  await storeAgentKnowledge(agentUid, communityUid, updatedKnowledge);

  // Step 5: Update agent preferences based on learning
  const preferences = await getAgentPreferences(agentUid, communityUid);
  const updatedPreferences = {
    ...preferences,
    adaptiveSettings: {
      ...preferences.adaptiveSettings,
      responseStyle: patterns.preferredResponseStyle,
      moderationSensitivity: patterns.moderationPreference,
      engagementLevel: patterns.optimalEngagementLevel
    }
  };

  await storeAgentPreferences(agentUid, communityUid, updatedPreferences);

  console.log("✅ Community knowledge updated with new patterns");
  return updatedKnowledge;
};

// Helper function to analyze community patterns
const analyzeCommunityPatterns = (data) => {
  // This would typically use ML algorithms to identify patterns
  // For this example, we'll use simple statistical analysis
  
  return {
    preferredResponseStyle: data.interactions.reduce((acc, interaction) => {
      // Analyze which response styles get better engagement
      return interaction.engagement > 0.7 ? interaction.style : acc;
    }, "friendly"),
    
    moderationPreference: data.moderationEvents.length > 10 ? "strict" : "moderate",
    
    optimalEngagementLevel: data.interactions.reduce((sum, i) => sum + i.engagement, 0) / data.interactions.length,
    
    peakActivityHours: data.activityByHour.reduce((peak, hour, index) => 
      hour > data.activityByHour[peak] ? index : peak, 0
    ),
    
    commonTopics: data.messages.reduce((topics, message) => {
      message.topics.forEach(topic => {
        topics[topic] = (topics[topic] || 0) + 1;
      });
      return topics;
    }, {})
  };
};
```

## Permission Management

### Scenario 1: Dynamic Permission Adjustment

```javascript
// Example of adjusting agent permissions based on performance
const adjustAgentPermissions = async (agentUid, communityUid, performanceData) => {
  console.log("⚙️ Adjusting agent permissions based on performance...");

  // Step 1: Get current assignment and permissions
  const assignments = await getAgentAssignments(agentUid);
  const currentAssignment = assignments.find(a => 
    a.community.uid === communityUid && a.isActive
  );

  if (!currentAssignment) {
    console.error("❌ No active assignment found");
    return null;
  }

  // Step 2: Analyze performance metrics
  const performanceScore = calculatePerformanceScore(performanceData);
  const recommendedPermissions = recommendPermissions(performanceScore, currentAssignment.permissions);

  // Step 3: Update permissions if changes are needed
  if (JSON.stringify(recommendedPermissions.sort()) !== JSON.stringify(currentAssignment.permissions.sort())) {
    const updateResult = await updateAgentAssignment(currentAssignment.uid, {
      permissions: recommendedPermissions,
      notes: `Permissions adjusted based on performance score: ${performanceScore}`
    });

    if (updateResult.success) {
      console.log("✅ Permissions updated successfully");
      console.log("Old permissions:", currentAssignment.permissions);
      console.log("New permissions:", recommendedPermissions);

      // Log the permission change
      await logAgentAction(agentUid, communityUid, {
        actionType: "permissions_adjusted",
        details: {
          oldPermissions: currentAssignment.permissions,
          newPermissions: recommendedPermissions,
          performanceScore,
          reason: "automatic_adjustment"
        },
        success: true
      });

      return updateResult.assignment;
    } else {
      console.error("❌ Failed to update permissions:", updateResult.errors);
      return null;
    }
  } else {
    console.log("ℹ️ No permission changes needed");
    return currentAssignment;
  }
};

// Helper function to calculate performance score
const calculatePerformanceScore = (data) => {
  const weights = {
    successRate: 0.3,
    responseTime: 0.2,
    userSatisfaction: 0.3,
    moderationAccuracy: 0.2
  };

  return (
    data.successRate * weights.successRate +
    (1 - data.averageResponseTime / 1000) * weights.responseTime + // Normalize response time
    data.userSatisfaction * weights.userSatisfaction +
    data.moderationAccuracy * weights.moderationAccuracy
  );
};

// Helper function to recommend permissions based on performance
const recommendPermissions = (score, currentPermissions) => {
  const basePermissions = ["send_messages"];
  
  if (score >= 0.9) {
    return [...basePermissions, "edit_community", "moderate_users", "manage_events", "ban_users"];
  } else if (score >= 0.7) {
    return [...basePermissions, "edit_community", "moderate_users", "manage_events"];
  } else if (score >= 0.5) {
    return [...basePermissions, "moderate_users"];
  } else {
    return basePermissions;
  }
};
```

### Scenario 2: Temporary Permission Elevation

```javascript
// Example of temporarily elevating permissions for specific tasks
const temporaryPermissionElevation = async (agentUid, communityUid, elevationRequest) => {
  console.log("🔐 Processing temporary permission elevation request...");

  // Step 1: Validate elevation request
  if (!validateElevationRequest(elevationRequest)) {
    console.error("❌ Invalid elevation request");
    return null;
  }

  // Step 2: Get current assignment
  const assignments = await getAgentAssignments(agentUid);
  const currentAssignment = assignments.find(a => 
    a.community.uid === communityUid && a.isActive
  );

  if (!currentAssignment) {
    console.error("❌ No active assignment found");
    return null;
  }

  // Step 3: Create temporary permission set
  const temporaryPermissions = [
    ...currentAssignment.permissions,
    ...elevationRequest.additionalPermissions
  ];

  // Step 4: Update assignment with temporary permissions
  const updateResult = await updateAgentAssignment(currentAssignment.uid, {
    permissions: temporaryPermissions,
    notes: `Temporary elevation: ${elevationRequest.reason} (expires: ${elevationRequest.expiresAt})`
  });

  if (!updateResult.success) {
    console.error("❌ Failed to elevate permissions:", updateResult.errors);
    return null;
  }

  // Step 5: Schedule permission restoration
  const restorationJob = schedulePermissionRestoration(
    currentAssignment.uid,
    currentAssignment.permissions,
    elevationRequest.expiresAt
  );

  // Step 6: Log the elevation
  await logAgentAction(agentUid, communityUid, {
    actionType: "permissions_elevated",
    details: {
      originalPermissions: currentAssignment.permissions,
      temporaryPermissions,
      reason: elevationRequest.reason,
      expiresAt: elevationRequest.expiresAt,
      restorationJobId: restorationJob.id
    },
    success: true
  });

  console.log("✅ Permissions temporarily elevated");
  console.log("Additional permissions:", elevationRequest.additionalPermissions);
  console.log("Expires at:", elevationRequest.expiresAt);

  return {
    assignment: updateResult.assignment,
    restorationJob
  };
};

// Helper function to validate elevation requests
const validateElevationRequest = (request) => {
  const requiredFields = ['additionalPermissions', 'reason', 'expiresAt', 'requestedBy'];
  
  if (!requiredFields.every(field => request[field])) {
    return false;
  }

  // Check if expiration is reasonable (not more than 24 hours)
  const expirationTime = new Date(request.expiresAt);
  const maxExpiration = new Date(Date.now() + 24 * 60 * 60 * 1000);
  
  if (expirationTime > maxExpiration) {
    return false;
  }

  return true;
};
```

## Bulk Operations

### Scenario 1: Bulk Agent Creation for Multiple Communities

```javascript
// Example of creating multiple agents for different communities
const bulkCreateCommunityAgents = async (communityAgentSpecs, creatorUid) => {
  console.log("🏭 Starting bulk agent creation...");

  const results = {
    successful: [],
    failed: [],
    assignments: []
  };

  for (const spec of communityAgentSpecs) {
    try {
      console.log(`Creating agent for community: ${spec.communityName}`);

      // Step 1: Create agent
      const agent = await createAgent({
        name: `${spec.communityName} AI ${spec.agentType}`,
        agentType: spec.agentType,
        capabilities: spec.capabilities,
        description: `AI ${spec.agentType.toLowerCase()} for ${spec.communityName}`,
        createdByUid: creatorUid
      });

      if (!agent) {
        results.failed.push({
          communityUid: spec.communityUid,
          error: "Failed to create agent"
        });
        continue;
      }

      results.successful.push(agent);

      // Step 2: Assign to community if specified
      if (spec.autoAssign) {
        const assignment = await assignAgentToManageCommunity(
          agent.uid,
          spec.communityUid,
          creatorUid
        );

        if (assignment) {
          results.assignments.push(assignment);

          // Step 3: Initialize with community-specific context
          if (spec.initialContext) {
            await storeAgentContext(agent.uid, spec.communityUid, spec.initialContext);
          }
        } else {
          console.warn(`⚠️ Agent created but assignment failed for ${spec.communityName}`);
        }
      }

      // Add delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));

    } catch (error) {
      console.error(`❌ Failed to process ${spec.communityName}:`, error);
      results.failed.push({
        communityUid: spec.communityUid,
        error: error.message
      });
    }
  }

  console.log("✅ Bulk creation completed");
  console.log(`Successful: ${results.successful.length}`);
  console.log(`Failed: ${results.failed.length}`);
  console.log(`Assignments: ${results.assignments.length}`);

  return results;
};

// Example usage
const communitySpecs = [
  {
    communityUid: "tech-community-123",
    communityName: "Tech Enthusiasts",
    agentType: "COMMUNITY_LEADER",
    capabilities: ["edit_community", "moderate_users", "manage_events", "send_messages"],
    autoAssign: true,
    initialContext: {
      focus: "technology_discussions",
      moderationStyle: "technical_accuracy",
      eventTypes: ["tech_talks", "code_reviews", "hackathons"]
    }
  },
  {
    communityUid: "gaming-community-456",
    communityName: "Gaming Hub",
    agentType: "MODERATOR",
    capabilities: ["moderate_users", "send_messages"],
    autoAssign: true,
    initialContext: {
      focus: "gaming_content",
      moderationStyle: "community_friendly",
      specialRules: ["no_spoilers", "respectful_competition"]
    }
  }
];

// Execute bulk creation
const bulkResults = await bulkCreateCommunityAgents(communitySpecs, "admin-user-123");
```

### Scenario 2: Bulk Permission Updates

```javascript
// Example of updating permissions for multiple agents
const bulkUpdateAgentPermissions = async (permissionUpdates, updatedByUid) => {
  console.log("🔧 Starting bulk permission updates...");

  const results = {
    successful: [],
    failed: [],
    summary: {}
  };

  for (const update of permissionUpdates) {
    try {
      console.log(`Updating permissions for agent: ${update.agentUid}`);

      // Step 1: Get current assignments
      const assignments = await getAgentAssignments(update.agentUid);
      const targetAssignment = assignments.find(a => 
        a.community.uid === update.communityUid && a.isActive
      );

      if (!targetAssignment) {
        results.failed.push({
          agentUid: update.agentUid,
          communityUid: update.communityUid,
          error: "No active assignment found"
        });
        continue;
      }

      // Step 2: Calculate new permissions
      let newPermissions;
      switch (update.operation) {
        case "add":
          newPermissions = [...new Set([...targetAssignment.permissions, ...update.permissions])];
          break;
        case "remove":
          newPermissions = targetAssignment.permissions.filter(p => !update.permissions.includes(p));
          break;
        case "replace":
          newPermissions = update.permissions;
          break;
        default:
          throw new Error(`Invalid operation: ${update.operation}`);
      }

      // Step 3: Update assignment
      const updateResult = await updateAgentAssignment(targetAssignment.uid, {
        permissions: newPermissions,
        notes: `Bulk update: ${update.operation} permissions - ${update.reason || 'No reason provided'}`
      });

      if (updateResult.success) {
        results.successful.push({
          agentUid: update.agentUid,
          communityUid: update.communityUid,
          oldPermissions: targetAssignment.permissions,
          newPermissions,
          operation: update.operation
        });

        // Log the change
        await logAgentAction(update.agentUid, update.communityUid, {
          actionType: "bulk_permission_update",
          details: {
            operation: update.operation,
            oldPermissions: targetAssignment.permissions,
            newPermissions,
            updatedBy: updatedByUid,
            reason: update.reason
          },
          success: true
        });
      } else {
        results.failed.push({
          agentUid: update.agentUid,
          communityUid: update.communityUid,
          error: updateResult.errors.join(", ")
        });
      }

      // Add delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 50));

    } catch (error) {
      console.error(`❌ Failed to update ${update.agentUid}:`, error);
      results.failed.push({
        agentUid: update.agentUid,
        communityUid: update.communityUid,
        error: error.message
      });
    }
  }

  // Generate summary
  results.summary = {
    totalProcessed: permissionUpdates.length,
    successful: results.successful.length,
    failed: results.failed.length,
    operationBreakdown: results.successful.reduce((acc, result) => {
      acc[result.operation] = (acc[result.operation] || 0) + 1;
      return acc;
    }, {})
  };

  console.log("✅ Bulk permission updates completed");
  console.log("Summary:", results.summary);

  return results;
};
```

## Integration Examples

### Scenario 1: Webhook Integration

```javascript
// Example of handling webhook events from the agent system
const handleAgentWebhook = async (webhookPayload) => {
  console.log("🔗 Processing agent webhook:", webhookPayload.event_type);

  switch (webhookPayload.event_type) {
    case "agent.assigned":
      await handleAgentAssigned(webhookPayload.data);
      break;
    
    case "agent.action":
      await handleAgentAction(webhookPayload.data);
      break;
    
    case "user.moderated":
      await handleUserModerated(webhookPayload.data);
      break;
    
    case "community.updated":
      await handleCommunityUpdated(webhookPayload.data);
      break;
    
    default:
      console.log("ℹ️ Unhandled webhook event:", webhookPayload.event_type);
  }
};

const handleAgentAssigned = async (data) => {
  console.log("🤖 Agent assigned webhook received");
  
  // Update your application's state
  await updateCommunityStatus(data.community_uid, {
    hasAILeader: true,
    aiLeaderUid: data.agent_uid,
    assignedAt: data.timestamp
  });

  // Send welcome notification to community members
  await sendCommunityNotification(data.community_uid, {
    type: "ai_leader_assigned",
    message: "Your community now has an AI leader to help manage activities!",
    agentName: data.agent_name
  });

  // Initialize community dashboard with AI metrics
  await initializeAIDashboard(data.community_uid, data.agent_uid);
};

const handleAgentAction = async (data) => {
  console.log("⚡ Agent action webhook received");
  
  // Update real-time activity feed
  await updateActivityFeed(data.community_uid, {
    type: "agent_action",
    agentUid: data.agent_uid,
    actionType: data.action_type,
    timestamp: data.timestamp,
    details: data.action_details
  });

  // Update community metrics
  await updateCommunityMetrics(data.community_uid, {
    lastAgentActivity: data.timestamp,
    agentActionCount: 1 // This would be incremented
  });

  // Handle specific action types
  if (data.action_type === "moderate_user") {
    await handleModerationAction(data);
  } else if (data.action_type === "edit_community") {
    await handleCommunityEdit(data);
  }
};
```

### Scenario 2: External AI Service Integration

```javascript
// Example of integrating with external AI services for enhanced capabilities
const enhanceAgentWithExternalAI = async (agentUid, communityUid, aiServiceConfig) => {
  console.log("🧠 Enhancing agent with external AI capabilities...");

  try {
    // Step 1: Initialize external AI service
    const aiService = new ExternalAIService(aiServiceConfig);
    await aiService.initialize();

    // Step 2: Get agent's current context and knowledge
    const currentContext = await getAgentContext(agentUid, communityUid);
    const communityKnowledge = await getCommunityKnowledge(agentUid, communityUid);

    // Step 3: Train/configure external AI with community data
    const trainingData = {
      communityContext: currentContext,
      knowledgeBase: communityKnowledge,
      communityRules: await getCommunityRules(communityUid),
      historicalData: await getCommunityHistory(communityUid, 30) // Last 30 days
    };

    const aiModel = await aiService.trainModel(trainingData);

    // Step 4: Store AI service configuration in agent preferences
    const preferences = await getAgentPreferences(agentUid, communityUid);
    const updatedPreferences = {
      ...preferences,
      externalAI: {
        serviceType: aiServiceConfig.type,
        modelId: aiModel.id,
        capabilities: aiModel.capabilities,
        configuredAt: new Date().toISOString(),
        enabled: true
      }
    };

    await storeAgentPreferences(agentUid, communityUid, updatedPreferences);

    // Step 5: Update agent capabilities to reflect AI enhancement
    const agent = await getAgent(agentUid);
    const enhancedCapabilities = [
      ...agent.capabilities,
      "ai_content_analysis",
      "sentiment_analysis",
      "advanced_moderation",
      "predictive_insights"
    ];

    await updateAgent(agentUid, {
      capabilities: enhancedCapabilities,
      description: `${agent.description} (Enhanced with ${aiServiceConfig.type} AI)`
    });

    console.log("✅ Agent successfully enhanced with external AI");
    return {
      aiModel,
      enhancedCapabilities,
      configuration: updatedPreferences.externalAI
    };

  } catch (error) {
    console.error("❌ Failed to enhance agent with external AI:", error);
    throw error;
  }
};

// Example external AI service class
class ExternalAIService {
  constructor(config) {
    this.config = config;
    this.apiKey = config.apiKey;
    this.endpoint = config.endpoint;
  }

  async initialize() {
    // Initialize connection to external AI service
    console.log("Initializing external AI service...");
  }

  async trainModel(trainingData) {
    // Train or configure the AI model with community-specific data
    console.log("Training AI model with community data...");
    
    // This would make actual API calls to the external service
    return {
      id: `model_${Date.now()}`,
      capabilities: ["content_analysis", "sentiment_detection", "moderation_assistance"],
      accuracy: 0.95,
      trainedAt: new Date().toISOString()
    };
  }

  async analyzeContent(content, context) {
    // Analyze content using the external AI service
    console.log("Analyzing content with external AI...");
    
    // This would make actual API calls
    return {
      sentiment: "neutral",
      toxicity: 0.1,
      topics: ["general_discussion"],
      moderationRecommendation: "approve",
      confidence: 0.92
    };
  }
}
```

## Troubleshooting Common Issues

### Issue 1: Agent Assignment Failures

```javascript
// Comprehensive troubleshooting for assignment failures
const troubleshootAssignmentFailure = async (agentUid, communityUid, assignerUid) => {
  console.log("🔍 Troubleshooting assignment failure...");

  const issues = [];
  const solutions = [];

  // Check 1: Agent exists and is active
  try {
    const agent = await getAgent(agentUid);
    if (!agent) {
      issues.push("Agent not found");
      solutions.push("Verify the agent UID is correct");
    } else if (!agent.isActive) {
      issues.push("Agent is not active");
      solutions.push("Activate the agent before assignment");
    }
  } catch (error) {
    issues.push("Failed to retrieve agent");
    solutions.push("Check agent service connectivity");
  }

  // Check 2: Community exists
  try {
    const community = await getCommunity(communityUid);
    if (!community) {
      issues.push("Community not found");
      solutions.push("Verify the community UID is correct");
    }
  } catch (error) {
    issues.push("Failed to retrieve community");
    solutions.push("Check community service connectivity");
  }

  // Check 3: Assigner has permissions
  try {
    const hasPermission = await checkUserPermission(assignerUid, communityUid, "assign_agents");
    if (!hasPermission) {
      issues.push("Assigner lacks permission to assign agents");
      solutions.push("Grant 'assign_agents' permission to the user");
    }
  } catch (error) {
    issues.push("Failed to check assigner permissions");
    solutions.push("Verify user permissions system");
  }

  // Check 4: Existing leader conflict
  try {
    const existingLeader = await getCommunityLeader(communityUid);
    if (existingLeader) {
      const agent = await getAgent(agentUid);
      if (agent && agent.agentType === "COMMUNITY_LEADER") {
        issues.push("Community already has a leader");
        solutions.push("Either deactivate existing leader or use allowMultipleLeaders: true");
      }
    }
  } catch (error) {
    issues.push("Failed to check existing leader");
    solutions.push("Check community leader query");
  }

  // Check 5: Rate limiting
  const recentAssignments = await getRecentAssignments(assignerUid, 1); // Last hour
  if (recentAssignments.length >= 50) {
    issues.push("Rate limit exceeded");
    solutions.push("Wait before making more assignments or contact support for limit increase");
  }

  // Generate report
  const report = {
    agentUid,
    communityUid,
    assignerUid,
    timestamp: new Date().toISOString(),
    issues,
    solutions,
    canProceed: issues.length === 0
  };

  console.log("🔍 Troubleshooting complete");
  console.log(`Issues found: ${issues.length}`);
  
  if (issues.length > 0) {
    console.log("Issues:", issues);
    console.log("Solutions:", solutions);
  } else {
    console.log("✅ No issues found - assignment should succeed");
  }

  return report;
};
```

### Issue 2: Memory and Context Problems

```javascript
// Troubleshooting memory and context issues
const troubleshootMemoryIssues = async (agentUid, communityUid) => {
  console.log("🧠 Troubleshooting memory issues...");

  const diagnostics = {
    memoryStats: {},
    issues: [],
    recommendations: []
  };

  try {
    // Check memory usage
    const memoryStats = await getAgentMemoryStats(agentUid, communityUid);
    diagnostics.memoryStats = memoryStats;

    // Check for common issues
    if (memoryStats.totalSize > 10 * 1024 * 1024) { // 10MB
      diagnostics.issues.push("Memory usage is very high");
      diagnostics.recommendations.push("Consider clearing old memory or reducing context size");
    }

    if (memoryStats.expiredCount > 100) {
      diagnostics.issues.push("Many expired memory entries");
      diagnostics.recommendations.push("Run memory cleanup to remove expired entries");
    }

    if (memoryStats.averageRetrievalTime > 1000) { // 1 second
      diagnostics.issues.push("Memory retrieval is slow");
      diagnostics.recommendations.push("Consider optimizing memory queries or reducing data size");
    }

    // Check context integrity
    const context = await getAgentContext(agentUid, communityUid);
    if (!context || Object.keys(context).length === 0) {
      diagnostics.issues.push("No context found for agent");
      diagnostics.recommendations.push("Initialize agent context with basic information");
    } else {
      // Validate context structure
      const requiredFields = ["lastActivity", "preferences", "stats"];
      const missingFields = requiredFields.filter(field => !context[field]);
      
      if (missingFields.length > 0) {
        diagnostics.issues.push(`Missing context fields: ${missingFields.join(", ")}`);
        diagnostics.recommendations.push("Reinitialize context with required fields");
      }
    }

    // Check conversation history
    const conversationHistory = await getConversationHistory(agentUid, communityUid, 1);
    if (conversationHistory.length === 0) {
      diagnostics.issues.push("No conversation history found");
      diagnostics.recommendations.push("This may be normal for new agents");
    }

    // Auto-fix some issues
    if (diagnostics.issues.includes("Many expired memory entries")) {
      console.log("🧹 Auto-cleaning expired memory entries...");
      const cleanedCount = await clearExpiredMemory(agentUid, communityUid);
      diagnostics.autoFixes = [`Cleaned ${cleanedCount} expired memory entries`];
    }

  } catch (error) {
    diagnostics.issues.push(`Memory system error: ${error.message}`);
    diagnostics.recommendations.push("Check memory service connectivity and logs");
  }

  console.log("🧠 Memory diagnostics complete");
  console.log(`Issues found: ${diagnostics.issues.length}`);
  
  return diagnostics;
};

// Helper function to clear expired memory
const clearExpiredMemory = async (agentUid, communityUid) => {
  const clearedCount = await clearAgentMemory(agentUid, communityUid, "expired");
  return clearedCount;
};
```

### Issue 3: Permission and Authentication Problems

```javascript
// Comprehensive permission troubleshooting
const troubleshootPermissionIssues = async (agentUid, communityUid, requiredPermission) => {
  console.log("🔐 Troubleshooting permission issues...");

  const diagnosis = {
    agentUid,
    communityUid,
    requiredPermission,
    checks: [],
    issues: [],
    solutions: []
  };

  // Check 1: Agent authentication
  try {
    const isAuthenticated = await authenticateAgent(agentUid, communityUid);
    diagnosis.checks.push({
      name: "Agent Authentication",
      status: isAuthenticated ? "PASS" : "FAIL",
      details: isAuthenticated ? "Agent is authenticated" : "Agent authentication failed"
    });

    if (!isAuthenticated) {
      diagnosis.issues.push("Agent is not authenticated");
      diagnosis.solutions.push("Verify agent is assigned to the community and assignment is active");
    }
  } catch (error) {
    diagnosis.checks.push({
      name: "Agent Authentication",
      status: "ERROR",
      details: error.message
    });
    diagnosis.issues.push("Authentication check failed");
    diagnosis.solutions.push("Check authentication service connectivity");
  }

  // Check 2: Assignment status
  try {
    const assignments = await getAgentAssignments(agentUid);
    const activeAssignment = assignments.find(a => 
      a.community.uid === communityUid && a.isActive
    );

    diagnosis.checks.push({
      name: "Active Assignment",
      status: activeAssignment ? "PASS" : "FAIL",
      details: activeAssignment ? 
        `Assignment found: ${activeAssignment.uid}` : 
        "No active assignment found"
    });

    if (!activeAssignment) {
      diagnosis.issues.push("No active assignment to community");
      diagnosis.solutions.push("Create an active assignment for the agent to this community");
    }
  } catch (error) {
    diagnosis.checks.push({
      name: "Active Assignment",
      status: "ERROR",
      details: error.message
    });
  }

  // Check 3: Specific permission
  if (requiredPermission) {
    try {
      const hasPermission = await validateAgentPermission(agentUid, communityUid, requiredPermission);
      diagnosis.checks.push({
        name: `Permission: ${requiredPermission}`,
        status: hasPermission ? "PASS" : "FAIL",
        details: hasPermission ? 
          "Permission granted" : 
          "Permission denied"
      });

      if (!hasPermission) {
        diagnosis.issues.push(`Missing required permission: ${requiredPermission}`);
        diagnosis.solutions.push(`Grant '${requiredPermission}' capability to agent or assignment`);
      }
    } catch (error) {
      diagnosis.checks.push({
        name: `Permission: ${requiredPermission}`,
        status: "ERROR",
        details: error.message
      });
    }
  }

  // Check 4: Agent capabilities
  try {
    const agent = await getAgent(agentUid);
    if (agent) {
      diagnosis.checks.push({
        name: "Agent Capabilities",
        status: "PASS",
        details: `Capabilities: ${agent.capabilities.join(", ")}`
      });

      if (requiredPermission && !agent.capabilities.includes(requiredPermission)) {
        diagnosis.issues.push(`Agent lacks capability: ${requiredPermission}`);
        diagnosis.solutions.push(`Add '${requiredPermission}' to agent capabilities`);
      }
    }
  } catch (error) {
    diagnosis.checks.push({
      name: "Agent Capabilities",
      status: "ERROR",
      details: error.message
    });
  }

  // Generate summary
  diagnosis.summary = {
    totalChecks: diagnosis.checks.length,
    passed: diagnosis.checks.filter(c => c.status === "PASS").length,
    failed: diagnosis.checks.filter(c => c.status === "FAIL").length,
    errors: diagnosis.checks.filter(c => c.status === "ERROR").length,
    canProceed: diagnosis.issues.length === 0
  };

  console.log("🔐 Permission diagnostics complete");
  console.log(`Checks: ${diagnosis.summary.passed}/${diagnosis.summary.totalChecks} passed`);
  
  if (diagnosis.issues.length > 0) {
    console.log("Issues:", diagnosis.issues);
    console.log("Solutions:", diagnosis.solutions);
  }

  return diagnosis;
};
```

These examples demonstrate real-world usage patterns and provide practical solutions for common scenarios when working with the Agentic Community Management system. Each example includes error handling, logging, and best practices for production use.