# Connection Module

## Overview

The **Connection** module is a sophisticated social networking system for managing user relationships on the Ooumph platform. It supports connection creation, relationship categorization, AI-powered recommendations, and real-time notifications — all through a privacy-first, circle-based architecture.

---

## Architecture

### Core Components

- **Models**: Neo4j and Django models for persistence  
- **GraphQL API**: Queries and mutations for client communication  
- **Services**: Notification and external integration logic  
- **Utils**: Decorators, helpers, and relation utilities  
- **Admin Interface**: Django admin support for managing relationships  

---

## Data Models

### Primary Connection Models

#### `Connection` (Legacy)
- Manages sender ↔ receiver relationships
- Statuses: `Received`, `Accepted`, `Rejected`, `Cancelled`
- Integrated with privacy circles for access control

#### `ConnectionV2` (Enhanced)
- Improved analytics and circle integration
- JSON-based dynamic relationship data
- Fully backward compatible

---

### Circle Models

#### `Circle` (Legacy)
- Types: `Outer`, `Inner`, `Universal`
- Defines relationship context and access control
- Supports nested sub-relations

#### `CircleV2` (Enhanced)
- JSON-based structure for per-user dynamic data
- Tracks relationship changes over time
- Enables evolving connection types

---

### Relationship Management Models

#### `Relation`
- Django model for broad categories: `Family`, `Friends`, `Professional`
- Supports hierarchical grouping

#### `SubRelation`
- Specific mappings like `Father → Child`, `Manager → Employee`
- Supports:
  - **Directionality**: Uni-/Bidirectional
  - **Approval**: Requires mutual confirmation
  - **Reverse Mapping**: Auto-creates reciprocal relations

---

## GraphQL API

### Schema Structure (`schema.py`)
- **Legacy**: `ConnectionQuery`, `ConnectionMutation`  
- **Enhanced V2**: `ConnectionQueryV2`, `ConnectionMutationV2`

### GraphQL Types

#### Core Types
- `ConnectionType`, `ConnectionV2Type`  
- `CircleType`, `CircleV2Type`  

#### User Discovery Types
- `RecommendedUserType`, `UserCategoryType`, `RecommendedUserForCommunityType`  

#### Relationship Types
- `RelationType`, `SubRelationType`  
- `StatusEnum`, `CircleTypeEnum`  

---

### Queries

#### User Discovery
- `recommended_users`
- `my_users_feed`
- `recommended_users_for_community`

#### Connection Management
- `my_connection`
- `connection_byuid`
- `connection_details_by_user_id`
- `my_sent_connection`

#### Relationship Data
- `all_relations`
- `relation`
- `grouped_connections_by_relation`

#### Administrative
- `all_connections` (admin only)

---

### Mutations

#### Connection Lifecycle
- `CreateConnection`, `UpdateConnection`, `DeleteConnection`
- `CreateConnectionV2`, `UpdateConnectionV2`

#### Circle Management
- Assign circle during connection creation  
- Dynamically update circles  
- Track relationship evolution  

---

## Services

### Notification Service (`notification_service.py`)

#### Features
- **Connection Requests**: Real-time alerts for requests
- **Status Updates**: Accepted or rejected connection notifications
- **Push Notifications**: Mobile-friendly messaging
- **Async Support**: Background delivery for better performance

#### Key Methods
- `notifyConnectionRequest`
- `notifyConnectionAccepted`
- `notifyConnectionRejected`

---

## Utilities

### Connection Decorator (`connection_decorator.py`)
- JWT-based authentication validation  
- Standardized GraphQL error responses  
- Permission and exception handling  

### Relation Utilities (`relation.py`)
- Lookup helper for relation/subrelation data  
- Validates relationships and reverse mappings  
- Simplifies relationship transformation logic  

---

## Key Features

### 1. Hierarchical Relationship System
- Circle-based privacy: `Outer`, `Inner`, `Universal`  
- Relationship types with approval, direction, and reverse logic  
- Dynamic relationship evolution with history tracking  

### 2. Advanced User Discovery
- AI/ML-based user suggestions  
- Filters: Location, interests, mutuals  
- Categorized and community-specific feeds  

### 3. Real-Time Notifications
- Instant push alerts for connection actions  
- Mobile device optimization  
- Asynchronous and non-blocking delivery  

### 4. Flexible Data Architecture
- Support for both legacy and V2 models  
- JSON-based dynamic properties  
- Relationship change analytics  

### 5. Privacy & Security
- Circle-based access and visibility  
- JWT-authenticated operations  
- Permission validation and secure error responses  

---

## Security & Authentication

### Authentication
- All GraphQL actions require **JWT tokens**  
- User context is tied to every request  
- Automatic token validation

### Authorization
- Users can modify only their own connections  
- Circle-based access restrictions  
- Superuser/admin override support

### Data Protection
- Full input validation  
- Secure error handling and response sanitation  
- Multi-layered permission checks  

---

## Database Integration

### Neo4j
- Natural graph-based connection mapping  
- Real-time updates using **Cypher**  
- Optimized for recommendations and relationship depth traversal  

### Django ORM
- Manages structured relationship metadata  
- Migration support and admin interface integration  

---

## External Integrations

### Notification Service
- Push notification integration (mobile/web)  
- RESTful API for delivery  
- Async + retry logic with error handling  

### Auth Manager
- Centralized user data integration  
- Real-time access to profiles and stats  
- Tracks live connection counts  

---

## Development Considerations

### Performance Optimization
- Optimized Cypher queries  
- Caching strategy to reduce DB hits  
- Async notifications  
- Pagination and batching for large datasets  

### Scalability
- Neo4j GraphDB for high-scale relationships  
- Modular microservice-ready architecture  
- Support for legacy and V2 APIs simultaneously  

### Code Quality
- Type-safe GraphQL schemas  
- Robust error handling  
- Inline documentation for maintainability  
- Unit tests for critical paths  

---

## Conclusion

The **Connection Module** is a scalable, secure, and intelligent engine for building modern social networks. It enables dynamic relationship management, real-time communication, and personalized discovery—all integrated into a flexible backend architecture built for performance.


