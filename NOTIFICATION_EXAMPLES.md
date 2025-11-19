# Example Notification Implementations

This file shows complete, working examples of how to add notifications to your most common mutations.

## Table of Contents
1. [Post Mutations](#post-mutations)
2. [Connection Mutations](#connection-mutations)
3. [Community Mutations](#community-mutations)
4. [Message Mutations](#message-mutations)
5. [Story Mutations](#story-mutations)
6. [Profile Mutations](#profile-mutations)

---

## Post Mutations

### Example 1: CreateComment Mutation

**File**: `post/graphql/mutations.py`

```python
class CreateComment(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    comment = graphene.Field(CommentType)

    class Arguments:
        input = CreateCommentInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        post_uid = input.post_uid
        text = input.text
        
        # Validate post exists
        post = Post.nodes.get_or_none(uid=post_uid)
        if not post:
            raise GraphQLError("Post not found")
        
        # Create comment
        comment = Comment(
            text=text,
            created_at=timezone.now()
        ).save()
        
        # Connect comment to post and user
        comment.post.connect(post)
        comment.creator.connect(user)
        
        # Handle mentions if any
        if input.mentioned_users:
            mention_service = MentionService()
            mention_service.process_mentions(
                content=text,
                mentioned_uids=input.mentioned_users,
                commenter=user,
                post=post
            )
        
        # Increment comment count
        increment_post_comment_count(post.uid)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Get post creator
            post_creator = post.creator.get()
            
            # Only notify if post creator is not the commenter
            if post_creator.device_id and post_creator.uid != user.uid:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_comment_on_post",
                    recipients=[{
                        'device_id': post_creator.device_id,
                        'uid': post_creator.uid
                    }],
                    username=user.username,
                    comment_text=text[:100],  # Truncate to 100 chars
                    post_id=post.uid,
                    comment_id=comment.uid
                )
        except Exception as e:
            # Log error but don't fail the mutation
            logger.error(f"Failed to send comment notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return CreateComment(
            success=True,
            message=PostMessages.COMMENT_CREATED,
            comment=comment
        )
```

### Example 2: CreatePost Mutation

**File**: `post/graphql/mutations.py`

```python
class CreatePost(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    post = graphene.Field(PostType)

    class Arguments:
        input = CreatePostInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        # Create post
        post = Post(
            title=input.title,
            text=input.text,
            post_type=input.post_type,
            privacy=input.privacy,
            created_at=timezone.now()
        ).save()
        
        # Connect to creator
        post.creator.connect(user)
        
        # Handle media files
        if input.file_ids:
            for file_id in input.file_ids:
                file = File.nodes.get(uid=file_id)
                post.files.connect(file)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Get user's followers/connections
            followers = user.followers.all()
            
            # Build recipient list
            recipients = []
            for follower in followers:
                if follower.device_id:
                    recipients.append({
                        'device_id': follower.device_id,
                        'uid': follower.uid
                    })
            
            # Send notification to all followers
            if recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_post_from_connection",
                    recipients=recipients,
                    username=user.username,
                    post_title=input.title[:50] if input.title else "New post",
                    post_id=post.uid
                )
        except Exception as e:
            logger.error(f"Failed to send post notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return CreatePost(
            success=True,
            message=PostMessages.POST_CREATED,
            post=post
        )
```

### Example 3: CreateLike/Vibe Mutation

**File**: `post/graphql/mutations.py`

```python
class CreateLike(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        post_uid = graphene.String(required=True)
        vibe_type = graphene.String(required=True)

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, post_uid, vibe_type):
        user = info.context.user
        
        # Get post
        post = Post.nodes.get_or_none(uid=post_uid)
        if not post:
            raise GraphQLError("Post not found")
        
        # Check if already liked
        existing_like = Like.nodes.get_or_none(
            uid=f"{user.uid}_{post_uid}"
        )
        
        if existing_like:
            raise GraphQLError("Already liked this post")
        
        # Create like
        like = Like(
            uid=f"{user.uid}_{post_uid}",
            vibe_type=vibe_type,
            created_at=timezone.now()
        ).save()
        
        # Connect relationships
        like.post.connect(post)
        like.user.connect(user)
        
        # Increment like count in Redis
        increment_post_like_count(post.uid)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Get post creator
            post_creator = post.creator.get()
            
            # Only notify if creator is not the liker
            if post_creator.device_id and post_creator.uid != user.uid:
                service = GlobalNotificationService()
                service.send(
                    event_type="vibe_reaction_on_post",
                    recipients=[{
                        'device_id': post_creator.device_id,
                        'uid': post_creator.uid
                    }],
                    username=user.username,
                    vibe_type=vibe_type,
                    post_id=post.uid
                )
        except Exception as e:
            logger.error(f"Failed to send like notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return CreateLike(
            success=True,
            message="Post liked successfully"
        )
```

---

## Connection Mutations

### Example 4: SendConnectionRequest Mutation

**File**: `connection/graphql/mutations.py`

```python
class SendConnectionRequest(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        receiver_uid = graphene.String(required=True)

    @login_required
    def mutate(self, info, receiver_uid):
        sender = info.context.user
        
        # Get receiver
        receiver = Users.nodes.get_or_none(uid=receiver_uid)
        if not receiver:
            raise GraphQLError("User not found")
        
        # Check if already connected
        if sender.connections.is_connected(receiver):
            raise GraphQLError("Already connected")
        
        # Check if request already exists
        existing_request = ConnectionRequest.nodes.get_or_none(
            sender_uid=sender.uid,
            receiver_uid=receiver_uid
        )
        
        if existing_request:
            raise GraphQLError("Request already sent")
        
        # Create connection request
        request = ConnectionRequest(
            sender_uid=sender.uid,
            receiver_uid=receiver_uid,
            status="pending",
            created_at=timezone.now()
        ).save()
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Notify receiver about new connection request
            if receiver.device_id:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_connection_request",
                    recipients=[{
                        'device_id': receiver.device_id,
                        'uid': receiver.uid
                    }],
                    username=sender.username,
                    sender_id=sender.uid,
                    request_id=request.uid
                )
        except Exception as e:
            logger.error(f"Failed to send connection request notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return SendConnectionRequest(
            success=True,
            message="Connection request sent"
        )
```

### Example 5: AcceptConnectionRequest Mutation

**File**: `connection/graphql/mutations.py`

```python
class AcceptConnectionRequest(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        request_uid = graphene.String(required=True)

    @login_required
    def mutate(self, info, request_uid):
        accepter = info.context.user
        
        # Get request
        request = ConnectionRequest.nodes.get_or_none(uid=request_uid)
        if not request:
            raise GraphQLError("Request not found")
        
        # Verify accepter is the receiver
        if request.receiver_uid != accepter.uid:
            raise GraphQLError("Unauthorized")
        
        # Get sender
        sender = Users.nodes.get(uid=request.sender_uid)
        
        # Create connection (both ways)
        accepter.connections.connect(sender)
        sender.connections.connect(accepter)
        
        # Update request status
        request.status = "accepted"
        request.save()
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Notify sender that their request was accepted
            if sender.device_id:
                service = GlobalNotificationService()
                service.send(
                    event_type="connection_accepted",
                    recipients=[{
                        'device_id': sender.device_id,
                        'uid': sender.uid
                    }],
                    username=accepter.username,
                    accepter_id=accepter.uid
                )
        except Exception as e:
            logger.error(f"Failed to send connection accepted notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return AcceptConnectionRequest(
            success=True,
            message="Connection accepted"
        )
```

---

## Community Mutations

### Example 6: CreateCommunityPost Mutation

**File**: `community/graphql/mutations.py`

```python
class CreateCommunityPost(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    post = graphene.Field(CommunityPostType)

    class Arguments:
        input = CreateCommunityPostInput()

    @handle_graphql_community_errors
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        community_uid = input.community_uid
        
        # Get community
        community = Community.nodes.get_or_none(uid=community_uid)
        if not community:
            raise GraphQLError("Community not found")
        
        # Check if user is member
        if not community.members.is_connected(user):
            raise GraphQLError("Not a community member")
        
        # Create post
        post = CommunityPost(
            title=input.title,
            content=input.content,
            post_type=input.post_type,
            created_at=timezone.now()
        ).save()
        
        # Connect relationships
        post.creator.connect(user)
        post.community.connect(community)
        
        # Handle files
        if input.file_ids:
            for file_id in input.file_ids:
                file = File.nodes.get(uid=file_id)
                post.files.connect(file)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Get all community members except the creator
            members = community.members.exclude(uid=user.uid)
            
            # Build recipient list
            recipients = []
            for member in members:
                if member.device_id:
                    recipients.append({
                        'device_id': member.device_id,
                        'uid': member.uid
                    })
            
            # Send notification to all members
            if recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_community_post",
                    recipients=recipients,
                    username=user.username,
                    community_name=community.name,
                    post_title=input.title[:50] if input.title else "New post",
                    post_id=post.uid,
                    community_id=community.uid
                )
        except Exception as e:
            logger.error(f"Failed to send community post notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return CreateCommunityPost(
            success=True,
            message=CommMessages.POST_CREATED,
            post=post
        )
```

### Example 7: JoinCommunity Mutation

**File**: `community/graphql/mutations.py`

```python
class JoinCommunity(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        community_uid = graphene.String(required=True)

    @handle_graphql_community_errors
    @login_required
    def mutate(self, info, community_uid):
        user = info.context.user
        
        # Get community
        community = Community.nodes.get_or_none(uid=community_uid)
        if not community:
            raise GraphQLError("Community not found")
        
        # Check if already member
        if community.members.is_connected(user):
            raise GraphQLError("Already a member")
        
        # Add user to community
        community.members.connect(user)
        
        # Add to Matrix room if exists
        if community.matrix_room_id:
            try:
                # Invite user to Matrix room
                matrix_profile = MatrixProfile.objects.get(user=user)
                invite_to_matrix_room(
                    room_id=community.matrix_room_id,
                    user_id=matrix_profile.matrix_user_id
                )
            except Exception as e:
                logger.error(f"Failed to invite to Matrix room: {e}")
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Notify the user who joined
            if user.device_id:
                service = GlobalNotificationService()
                service.send(
                    event_type="user_joined_community",
                    recipients=[{
                        'device_id': user.device_id,
                        'uid': user.uid
                    }],
                    username=user.username,
                    community_name=community.name,
                    community_id=community.uid
                )
            
            # Notify existing members about new member
            existing_members = community.members.exclude(uid=user.uid)
            member_recipients = []
            
            for member in existing_members:
                if member.device_id:
                    member_recipients.append({
                        'device_id': member.device_id,
                        'uid': member.uid
                    })
            
            if member_recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_members_joined_community",
                    recipients=member_recipients,
                    username=user.username,
                    community_name=community.name,
                    community_id=community.uid,
                    member_count=1
                )
        except Exception as e:
            logger.error(f"Failed to send join community notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return JoinCommunity(
            success=True,
            message=CommMessages.JOINED_COMMUNITY
        )
```

---

## Message Mutations

### Example 8: SendMessage Mutation

**File**: `msg/graphql/mutations.py`

```python
class SendMessage(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    sent_message = graphene.Field(MessageType)

    class Arguments:
        input = SendMessageInput()

    @login_required
    def mutate(self, info, input):
        sender = info.context.user
        receiver_uid = input.receiver_uid
        text = input.text
        
        # Get receiver
        receiver = Users.nodes.get_or_none(uid=receiver_uid)
        if not receiver:
            raise GraphQLError("User not found")
        
        # Create message
        message = Message(
            text=text,
            message_type=input.message_type,
            created_at=timezone.now(),
            is_read=False
        ).save()
        
        # Connect relationships
        message.sender.connect(sender)
        message.receiver.connect(receiver)
        
        # Get or create chat
        chat = get_or_create_chat(sender, receiver)
        message.chat.connect(chat)
        
        # Update chat last message time
        chat.last_message_at = timezone.now()
        chat.save()
        
        # Handle file attachments
        if input.file_ids:
            for file_id in input.file_ids:
                file = File.nodes.get(uid=file_id)
                message.files.connect(file)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Only notify if receiver is not the sender (shouldn't happen but safety check)
            if receiver.device_id and receiver.uid != sender.uid:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_message",
                    recipients=[{
                        'device_id': receiver.device_id,
                        'uid': receiver.uid
                    }],
                    username=sender.username,
                    message_preview=text[:100],  # First 100 chars
                    chat_id=chat.uid,
                    message_id=message.uid
                )
        except Exception as e:
            logger.error(f"Failed to send message notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return SendMessage(
            success=True,
            message="Message sent successfully",
            sent_message=message
        )
```

### Example 9: CreateGroupChat Mutation

**File**: `msg/graphql/mutations.py`

```python
class CreateGroupChat(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    group_chat = graphene.Field(GroupChatType)

    class Arguments:
        input = CreateGroupChatInput()

    @login_required
    def mutate(self, info, input):
        creator = info.context.user
        
        # Create group chat
        group_chat = GroupChat(
            name=input.name,
            description=input.description,
            created_at=timezone.now()
        ).save()
        
        # Connect creator
        group_chat.creator.connect(creator)
        group_chat.members.connect(creator)
        
        # Add members
        member_users = []
        for member_uid in input.member_uids:
            member = Users.nodes.get(uid=member_uid)
            group_chat.members.connect(member)
            member_users.append(member)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Notify all members except creator
            recipients = []
            for member in member_users:
                if member.device_id and member.uid != creator.uid:
                    recipients.append({
                        'device_id': member.device_id,
                        'uid': member.uid
                    })
            
            if recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_group_chat_created",
                    recipients=recipients,
                    group_name=input.name,
                    creator_name=creator.username,
                    group_id=group_chat.uid
                )
        except Exception as e:
            logger.error(f"Failed to send group chat notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return CreateGroupChat(
            success=True,
            message="Group chat created successfully",
            group_chat=group_chat
        )
```

---

## Story Mutations

### Example 10: CreateStory Mutation

**File**: `story/graphql/mutations.py`

```python
class CreateStory(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    story = graphene.Field(StoryType)

    class Arguments:
        input = CreateStoryInput()

    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        # Create story
        story = Story(
            story_type=input.story_type,
            duration=input.duration or 24,  # Default 24 hours
            created_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=input.duration or 24)
        ).save()
        
        # Connect creator
        story.creator.connect(user)
        
        # Handle media files
        if input.file_ids:
            for file_id in input.file_ids:
                file = File.nodes.get(uid=file_id)
                story.files.connect(file)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Get user's connections/followers
            connections = user.connections.all()
            
            # Build recipient list
            recipients = []
            for connection in connections:
                if connection.device_id:
                    recipients.append({
                        'device_id': connection.device_id,
                        'uid': connection.uid
                    })
            
            # Send notification to all connections
            if recipients:
                service = GlobalNotificationService()
                service.send(
                    event_type="new_story_from_connection",
                    recipients=recipients,
                    username=user.username,
                    story_id=story.uid
                )
        except Exception as e:
            logger.error(f"Failed to send story notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return CreateStory(
            success=True,
            message="Story created successfully",
            story=story
        )
```

---

## Profile Mutations

### Example 11: AddAchievement Mutation

**File**: `profile/graphql/mutations.py`

```python
class AddAchievement(Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    achievement = graphene.Field(AchievementType)

    class Arguments:
        input = AddAchievementInput()

    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        # Create achievement
        achievement = Achievement(
            name=input.name,
            description=input.description,
            date_achieved=input.date_achieved,
            created_at=timezone.now()
        ).save()
        
        # Connect to user
        user.achievements.connect(achievement)
        
        # Handle certificate/proof files
        if input.file_ids:
            for file_id in input.file_ids:
                file = File.nodes.get(uid=file_id)
                achievement.files.connect(file)
        
        # ============= NOTIFICATION CODE START =============
        from notification.global_service import GlobalNotificationService
        
        try:
            # Notify user about their achievement
            if user.device_id:
                service = GlobalNotificationService()
                service.send(
                    event_type="achievement_added",
                    recipients=[{
                        'device_id': user.device_id,
                        'uid': user.uid
                    }],
                    username=user.username,
                    achievement_name=input.name,
                    achievement_id=achievement.uid
                )
        except Exception as e:
            logger.error(f"Failed to send achievement notification: {e}")
        # ============= NOTIFICATION CODE END =============
        
        return AddAchievement(
            success=True,
            message="Achievement added successfully",
            achievement=achievement
        )
```

---

## Key Patterns to Remember

### 1. Always Check Device ID
```python
if user.device_id:
    # Send notification
```

### 2. Don't Notify Self
```python
if recipient.uid != sender.uid:
    # Send notification
```

### 3. Handle Errors Gracefully
```python
try:
    # Send notification
except Exception as e:
    logger.error(f"Notification error: {e}")
    # Don't fail the mutation
```

### 4. Batch Notifications
```python
# Good: One call for all recipients
recipients = [...]
service.send(event_type="...", recipients=recipients, ...)

# Bad: Loop with individual calls
for recipient in recipients:
    service.send(...)  # Don't do this
```

### 5. Import Once at Top
```python
# At top of file
from notification.global_service import GlobalNotificationService

# Not inside every mutation
```

---

## Testing Your Implementation

```python
# Test in Django shell
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{
        'device_id': 'your_test_device_id',
        'uid': 'test_user_uid'
    }],
    username="Test User",
    comment_text="Test comment",
    post_id="test_123"
)

# Check Django Admin
# Go to: /admin/notification/usernotification/
```

---

## Summary

These examples show the complete pattern for adding notifications to your mutations:

1. ✅ Import `GlobalNotificationService` at top of file
2. ✅ After successful operation, wrap notification code in try-except
3. ✅ Check recipient has device_id
4. ✅ Check recipient is not the actor (don't notify self)
5. ✅ Collect recipients into list for batch sends
6. ✅ Call `service.send()` with event_type and template variables
7. ✅ Log errors but don't fail the mutation

Copy these patterns and adapt them for your specific mutations!
