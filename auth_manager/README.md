# Auth Manager Module Documentation

## Overview

The `auth_manager` module is a comprehensive authentication and user management system for the Ooumph backend application. It provides user registration, authentication, profile management, and various user-related functionalities through a GraphQL API interface.

## Architecture

### Core Components

1. **Models** (`models.py`) - Neo4j-based data models for users and profiles
2. **GraphQL API** (`graphql/`) - Complete GraphQL schema with queries and mutations
3. **Services** (`services/`) - Business logic for OTP, email, and feedback
4. **Validators** (`validators/`) - Input validation and security rules
5. **Utils** (`Utils/`) - Helper functions and decorators
6. **Admin Interface** (`admin.py`) - Django admin configuration

## Data Models

### Primary Models

#### Users (Neo4j Node)
- **Purpose**: Core user entity with authentication data
- **Key Fields**:
  - `uid`: Unique identifier
  - `user_id`: Django User foreign key
  - `username`: Unique username
  - `email`: User email address
  - `first_name`, `last_name`: User names
  - `user_type`: Account type (personal, business, etc.)
- **Relationships**:
  - `HAS_PROFILE`: Links to Profile node
  - `HAS_CONNECTION_STAT`: Links to ConnectionStats
  - Various content relationships (posts, communities, etc.)

#### Profile (Neo4j Node)
- **Purpose**: Detailed user profile information
- **Key Fields**:
  - Personal: `gender`, `bio`, `born`, `dob`
  - Contact: `phone_number`, `device_id`, `fcm_token`
  - Location: `lives_in`, `city`, `state`
  - Professional: `designation`, `worksat`
  - Media: `profile_pic_id`, `cover_image_id`
- **Relationships**:
  - `HAS_ONBOARDING`: Onboarding status
  - `HAS_CONTACT_INFO`: Contact information
  - `HAS_SCORE`: User scoring metrics
  - `HAS_INTEREST`: User interests
  - `HAS_ACHIEVEMENT`: Achievements
  - `HAS_EDUCATION`: Education records
  - `HAS_SKILL`: Skills
  - `HAS_EXPERIENCE`: Work experience

#### Supporting Models

**OnboardingStatus**: Tracks user onboarding progress
- Fields: `email_verified`, `phone_verified`, `username_selected`, etc.

**ContactInfo**: User contact information
- Fields: `type`, `value`, `platform`, `link`

**Score**: User scoring and metrics
- Fields: `vibers_count`, `cumulative_vibescore`, `intelligence_score`, etc.

**Interest**: User interests and hobbies
- Fields: `names` (list of interest names)

**Achievement**: User achievements and accomplishments
- Fields: `what`, `from_source`, `description`, `from_date`, `to_date`, `file_id`

**Education**: Educational background
- Fields: `institution`, `degree`, `field_of_study`, `start_date`, `end_date`

**Skill**: User skills and competencies
- Fields: `name`, `proficiency_level`, `years_of_experience`

**Experience**: Work experience records
- Fields: `company`, `position`, `description`, `start_date`, `end_date`

### Django Models

**OTP**: One-time password management
- Fields: `user`, `otp`, `purpose`, `created_at`, `expires_at`

**UploadContact**: Contact list uploads
- Fields: `user`, `contact` (JSON array)

**Invite**: User invitation system
- Fields: `inviter`, `invite_token`, `origin_type`, `expiry_date`

**WelcomeScreenMessage**: App welcome messages
- Fields: `title`, `content`, `image`, `rank`, `is_visible`

**InterestList**: Predefined interest categories
- Fields: `name`, `sub_interests` (JSON structure)

**Location Models**: `CountryInfo`, `StateInfo`, `CityInfo`
- Geographic data for user locations

## GraphQL API

### Schema Structure

```python
# Main schemas
schema = graphene.Schema(query=Query, mutation=Mutation)
schemaV2 = graphene.Schema(query=QueryV2, mutation=Mutation)
```

### Key Types

#### User Types
- `UserType`: Basic user information
- `UserInfoType`: Enhanced user information (V2)
- `ProfileType`: Complete profile data
- `ProfileInfoType`: Comprehensive profile with statistics
- `MatrixUserType`: User with Matrix chat integration

#### Data Types
- `OnboardingStatusType`: Onboarding progress
- `ContactInfoType`: Contact information
- `ScoreType`: User scoring metrics
- `InterestType`: User interests
- `AchievementType`: Achievement records
- `EducationType`: Education records
- `SkillType`: Skill records
- `ExperienceType`: Experience records

### Queries

#### User Queries
- `all_users`: List all users (admin)
- `search_matrix_username`: Find user by username with Matrix info
- `profile_by_user_id`: Get user profile by ID
- `my_profile`: Get authenticated user's complete profile

#### Data Queries
- `my_onboarding`: Get onboarding status
- `my_contact_info`: Get contact information
- `my_score`: Get user scores
- `my_interests`: Get user interests
- `my_achievements`: Get achievements
- `my_education`: Get education records
- `my_skills`: Get skills
- `my_experience`: Get work experience

#### Discovery Queries
- `interest_lists`: Get available interest categories
- `welcome_messages`: Get welcome screen messages
- `my_connection_list_user`: Get users from uploaded contacts
- `my_invitation_list_user`: Get contacts available for invitation

### Mutations

#### Authentication
- `register_user`: Create new user account
- `register_userV2`: Enhanced user registration with invite support
- `login_by_username_email`: User authentication
- `logout`: User logout with cleanup
- `send_otp`: Send OTP for verification
- `verify_otp`: Verify OTP code
- `verify_otp_and_reset_password`: Password reset with OTP

#### Profile Management
- `update_user_profile`: Update profile information
- `select_username`: Set/update username
- `delete_user_account`: Delete user account
- `delete_user_profile`: Delete user profile

#### Data Management
- `Create_onboarding`: Create onboarding status
- `update_onboarding`: Update onboarding progress
- `add_contactinfo`: Add contact information
- `edit_contactinfo`: Update contact information
- `delete_contactinfo`: Remove contact information
- `add_score`: Create user score
- `update_score`: Update user score
- `add_interest`: Add user interests
- `edit_interest`: Update interests
- `delete_intrest`: Remove interests

#### Content Management
- `create_achievement`: Add achievement
- `update_achievement`: Update achievement
- `delete_achievement`: Remove achievement
- `create_education`: Add education record
- `update_education`: Update education
- `delete_education`: Remove education
- `create_skill`: Add skill
- `update_skill`: Update skill
- `delete_skill`: Remove skill
- `create_experience`: Add work experience
- `update_experience`: Update experience
- `delete_experience`: Remove experience

#### Social Features
- `create_user_review`: Create user review
- `delete_user_review`: Remove user review
- `create_back_profile_review`: Create profile review
- `create_profile_data_like`: Like profile data
- `create_profile_data_comment`: Comment on profile data

#### Utility Mutations
- `create_upload_contact`: Upload contact list
- `update_upload_contact`: Update uploaded contacts
- `delete_upload_contact`: Remove uploaded contacts
- `send_feedback`: Send user feedback
- `send_invite`: Send user invitation
- `search_username`: Search for available usernames

## Services

### OTP Service (`services/send_otp.py`)
- **Purpose**: Handle OTP generation and delivery
- **Features**:
  - Email OTP sending
  - SMS OTP sending (if configured)
  - OTP validation and expiry management
  - Multiple OTP purposes (password reset, email verification)

### Email Service (`services/email_template/`)
- **Purpose**: Email template management and sending
- **Features**:
  - HTML email templates
  - Dynamic payload generation
  - Email utility functions
  - Template customization

### Feedback Service (`services/feedback.py`)
- **Purpose**: User feedback collection and processing
- **Features**:
  - Feedback submission
  - Feedback categorization
  - Admin notification system

## Validation System

### Custom GraphQL Validators (`validators/custom_graphql_validator.py`)
- **Purpose**: Input validation for GraphQL operations
- **Features**:
  - Type-specific validation
  - Custom scalar types
  - Field-level validation rules
  - Error message customization

### Validation Rules (`validators/rules/`)

#### String Validation
- Username format validation
- Name validation (first/last name)
- Bio and description validation
- HTML content prevention
- Gender validation
- Job title and designation validation

#### Email Validation
- Email format verification
- Domain validation
- Disposable email detection

#### Password Validation
- Strength requirements
- Character composition rules
- Length constraints
- Common password prevention

#### Date Validation
- Date of birth validation
- Age restrictions
- Date format verification

#### User Validation
- Complete user input validation
- Cross-field validation
- Business rule enforcement

## Utilities

### Authentication Decorator (`Utils/auth_manager_decorator.py`)
- **Purpose**: Error handling for GraphQL resolvers
- **Features**:
  - Standardized error responses
  - Authentication validation
  - Permission checking
  - Exception handling

### Presigned URL Generator (`Utils/generate_presigned_url.py`)
- **Purpose**: Secure file access URL generation
- **Features**:
  - AWS S3 integration
  - Temporary URL generation
  - File metadata extraction
  - Security token management

### Username Suggestions (`Utils/generate_username_suggestions.py`)
- **Purpose**: Generate available username suggestions
- **Features**:
  - Intelligent username generation
  - Availability checking
  - Pattern-based suggestions
  - Uniqueness validation

### OTP Generator (`Utils/otp_generator.py`)
- **Purpose**: Secure OTP generation
- **Features**:
  - Cryptographically secure random generation
  - Configurable OTP length
  - Expiry time management
  - Purpose-specific OTPs

### Connection Count (`Utils/connection_count.py`)
- **Purpose**: User connection statistics
- **Features**:
  - Real-time connection counting
  - Statistics updates
  - Performance optimization
  - Cache management

## Key Features

### 1. Comprehensive User Management
- Complete user lifecycle management
- Profile customization and management
- Multi-step onboarding process
- Rich user data models

### 2. Advanced Authentication
- JWT-based authentication
- OTP verification system
- Password reset functionality
- Multi-factor authentication support

### 3. Social Features
- User reviews and ratings
- Profile data interactions (likes, comments)
- Interest-based user discovery
- Contact list integration

### 4. Professional Profiles
- Education history management
- Work experience tracking
- Skills and achievements
- Professional networking features

### 5. Matrix Chat Integration
- Seamless chat system integration
- Automatic Matrix account creation
- Profile synchronization
- Real-time messaging support

### 6. Invitation System
- Token-based invitations
- Automatic connection creation
- Expiry management
- Origin tracking

### 7. Content Management
- File upload and management
- Media processing
- Presigned URL generation
- Content validation

### 8. Analytics and Scoring
- User engagement metrics
- Scoring algorithms
- Performance tracking
- Statistical analysis

## Security & Authentication

### Authentication Methods
1. **JWT Tokens**: Primary authentication mechanism
2. **OTP Verification**: Two-factor authentication
3. **Password Policies**: Strong password requirements
4. **Session Management**: Secure session handling

### Security Features
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting
- Secure file uploads

### Data Protection
- Personal data encryption
- Secure password storage
- Privacy controls
- Data anonymization options

## Database Integration

### Neo4j Integration
- Graph-based user relationships
- Complex query optimization
- Real-time data updates
- Relationship management

### Django ORM
- Traditional relational data
- Admin interface integration
- Migration management
- Data consistency

## External Integrations

### Matrix Chat System
- Real-time messaging
- Room management
- User synchronization
- Authentication integration

### AWS S3
- File storage and management
- Presigned URL generation
- Media processing
- CDN integration

### Email Services
- SMTP integration
- Template management
- Delivery tracking
- Bounce handling

### SMS Services
- OTP delivery
- International support
- Delivery confirmation
- Cost optimization

## Development Considerations

### Performance
- Efficient Neo4j queries
- Caching strategies
- Database indexing
- Query optimization

### Scalability
- Horizontal scaling support
- Load balancing
- Database sharding
- Microservice architecture

### Testing
- Comprehensive test suite
- Unit tests for all components
- Integration tests
- Performance testing

### Code Quality
- Type hints and documentation
- Error handling
- Code organization
- Design patterns

## Configuration

### Environment Variables
- Database connections
- External service credentials
- Security settings
- Feature flags

### Settings Management
- Environment-specific configurations
- Secret management
- Feature toggles
- Performance tuning

## Monitoring & Logging

### Application Monitoring
- Performance metrics
- Error tracking
- User activity monitoring
- System health checks

### Logging
- Structured logging
- Log aggregation
- Security event logging
- Audit trails

## API Documentation

### GraphQL Schema
- Complete schema documentation
- Type definitions
- Query examples
- Mutation examples

### Error Handling
- Standardized error responses
- Error codes and messages
- Debugging information
- User-friendly error messages

## Deployment

### Docker Support
- Containerized deployment
- Multi-stage builds
- Environment configuration
- Health checks

### CI/CD Integration
- Automated testing
- Deployment pipelines
- Environment promotion
- Rollback strategies

## Future Enhancements

### Planned Features
- Enhanced social features
- Advanced analytics
- Mobile app integration
- Third-party integrations

### Technical Improvements
- Performance optimizations
- Security enhancements
- Code refactoring
- Documentation updates

