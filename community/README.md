# Community Module

## Overview

The **Community** module is a comprehensive system for managing communities, subcommunities, and associated features within the Ooumph backend. It provides a complete social platform infrastructure with support for messaging, elections, roles, memberships, and Matrix chat integration.

---

## Architecture

### Core Components

- **Models**: 25+ Neo4j-based models for data persistence  
- **GraphQL API**: Complete CRUD operations via GraphQL schema  
- **Services**: Notification and business logic services  
- **Utils**: Helper functions for Matrix integration, community generation, and data processing  
- **Admin Interface**: Django admin configuration (currently commented out)  

---

## Data Models

### Primary Models (`models.py`)

#### `Community`
- Core community entity with properties like `name`, `description`, `type`, and `visibility`
- Supports types: `PUBLIC`, `PRIVATE`, `INVITE_ONLY`
- Integrates with Matrix chat rooms for real-time messaging
- Tracks creation date, member count, and external integrations

#### `SubCommunity`
- Hierarchical subcommunities under main communities
- Inherits settings from the parent
- Independent member/role management

#### `Membership`
- Manages user participation in communities
- Tracks admin status, permissions, join dates, notification prefs, block status, leadership

#### `CommunityMessages`
- Internal message system for communication
- File attachment support
- Tracks metadata and interactions

---

### Governance Models

#### `Election`
- Supports democratic community leadership
- Multiple voting types, candidate management, result tracking

#### `Nomination` & `Vote`
- Secure candidate nomination
- Duplicate vote prevention and transparent voting

#### `Role` & `CommunityRole`
- Flexible role-based access control
- Custom roles with hierarchical permission structures

---

### Content & Engagement Models

#### `CommunityPost`
- User-generated posts (text, media)
- Integrated with reaction/comment systems

#### `CommunityProduct` & `CommunityStory`
- Product and story showcasing
- Enhances engagement and discoverability

#### `CommunityReview`
- Review and rating system for communities
- Moderation and feedback handling

---

### Management Models

- **`CommunityKeyword`**: SEO enhancement through tags  
- **`CommunityRule`**: Community guidelines and rule enforcement  
- **`CommunityUserBlock`**: Moderation tools like blocking and reporting  

---

## GraphQL API

### Schema Structure (`schema.py`)
Combines all queries and mutations for full API support.

### Types (`types.py`)
- `CommunityType`, `SubCommunityType`
- `MembershipType`, `CommunityMessagesType`
- `ElectionType`, `NominationType`, `VoteType`
- `CommunityPostType`

### Queries (`queries.py`)
- `resolve_community_byuid`: Fetch community/subcommunity details  
- `resolve_my_community`: Get user's joined communities  
- `resolve_grouped_communities`: Categorize communities by type  

> **Authentication required** for all queries  
> **Error Handling**: Via `handle_graphql_community_errors`

### Mutations (`mutations.py`)

#### Community Management
- `CreateCommunity`, `UpdateCommunity`, `DeleteCommunity`

#### Messaging
- `CreateCommunityMessage`: Supports file attachments and validation

#### Features
- Automatic Matrix room creation
- Push notification integration
- Member invitation processing
- Role-based permission enforcement

---

## Services

### Notification Service (`notification_service.py`)
- Community creation, member addition, subcommunity alerts
- Push notification support (async)

---

## Utilities

### Matrix Integration
- **Room Creation**: Auto room setup for new communities  
- **Member Invitations**: Bulk invite to Matrix rooms  
- **Token Management**: Secure Matrix access  

### Community Generation
- **Interest-Based Suggestions**: Community recommendations  
- **User Matching**: Algorithm-driven discovery  

### Helper Functions
- **User Validation**: Check if user can join  
- **Permission Validation**: Role/admin verification  
- **Data Processing**: Query optimization and transformation  

---

## Key Features

### ✅ Hierarchical Structure
- Unlimited subcommunities under main
- Inherited settings and roles

### 💬 Matrix Chat Integration
- Real-time messaging via Matrix
- Secure token-based auth
- Auto room creation & member invitation

### 🗳️ Democratic Governance
- Election system with nomination & voting
- Transparent leadership system

### 🛡️ Role-Based Access Control
- Custom role creation
- Hierarchical permissions

### 🧵 Content Management
- Support for media, posts, attachments
- Category-based content discovery

### 🚨 Safety & Moderation
- User blocking, reporting, and enforcement
- Community rules and guidelines

### 🔔 Notification System
- Real-time notifications via external service
- Event-driven and async processing

---

## Security & Authentication

- **JWT-based Authentication** for all GraphQL operations  
- **Role-based Authorization** for sensitive actions  
- **Creator Privileges**: Elevated permissions for community creators  
- **Input Validation**: Strict sanitization rules  
- **Error Handling**: Via `handle_graphql_community_errors`  

---

## Database Integration

- **Neo4j**: Graph database for community and relationship modeling  
- **Neomodel ORM**: Pythonic object-relational mapping  
- **Relationship Tracking**: Deep links between users, roles, and communities  
- **Query Optimization**: Efficient traversals and indexing  

---

## External Integrations

### Matrix Protocol
- Federated, end-to-end encrypted chat  
- Room management and real-time messaging  

### Push Notification Service
- Event-based triggers  
- Cross-platform support  

### File Storage
- S3-compatible  
- Presigned URL generation  
- Image validation & processing  

---

## Development Considerations

### 🔧 Performance Optimizations
- Async notifications and Matrix calls  
- Cached queries and reduced DB hits  

### 🚀 Scalability
- Microservice architecture  
- Horizontal scaling ready  
- Modular services  

### ✅ Code Quality
- Type hints  
- Logging and exception handling  
- Well-documented and modular code  

---

## Future Improvements
- Enhanced moderation dashboards  
- Community analytics  
- Deeper Matrix feature integrations  
- Community-level settings UI

---


