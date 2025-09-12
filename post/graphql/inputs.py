import graphene
from auth_manager.validators import custom_graphql_validator

class CreatePostInput(graphene.InputObjectType):
    post_title = custom_graphql_validator.SpecialCharacterString2_200.add_option("postTitle", "CreatePost")()
    post_text = custom_graphql_validator.NonSpecialCharacterString2_200.add_option("postText", "CreatePost")()
    post_type = custom_graphql_validator.String.add_option("postType", "CreatePost")()
    privacy = custom_graphql_validator.String.add_option("privacy", "CreatePost")()
    post_file_id=custom_graphql_validator.ListString.add_option("postFileId", "CreatePost")()
    tags = graphene.List(graphene.String, description="List of tags/keywords for post categorization")
    
class UpdatePostInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    post_title = custom_graphql_validator.SpecialCharacterString2_100.add_option("postTitle", "UpdatePost")()
    post_text = custom_graphql_validator.SpecialCharacterString2_200.add_option("postText", "UpdatePost")()
    post_type = custom_graphql_validator.String.add_option("postType", "UpdatePost")()
    privacy = custom_graphql_validator.String.add_option("privacy", "UpdatePost")()
    vibe_score = custom_graphql_validator.Float.add_option("vibeScore", "UpdatePost")()
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdatePost")()

class DeleteInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "DeletePost")(required=True)

class CreateTagInput(graphene.InputObjectType):
    names = custom_graphql_validator.ListString.add_option("names", "CreateTag")(required=True)
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreateTag")(required=True)

class UpdateTagInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateTag")(required=True)
    names = custom_graphql_validator.ListString.add_option("names", "UpdateTag")()
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateTag")()

class CreateCommentInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreateComment")(required=True)
    content = custom_graphql_validator.SpecialCharacterString2_100.add_option("content", "CreateComment")(required=True)
    parent_comment_uid = custom_graphql_validator.String.add_option("parentCommentUid", "CreateComment")()
    comment_file_id = custom_graphql_validator.ListString.add_option("commentFileId", "CreateComment")()


class UpdateCommentInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateComment")(required=True)
    content = custom_graphql_validator.NonSpecialCharacterString5_100.add_option("content", "UpdateComment")()
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateComment")()
    comment_file_id = custom_graphql_validator.ListString.add_option("commentFileId", "UpdateComment")()

class CreateLikeInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreateLike")(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateLike")()
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateLike")()

class UpdateLikeInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateLike")(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "UpdateLike")()
    vibe = custom_graphql_validator.Float.add_option("vibe", "UpdateLike")()
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateLike")()

class CreatePostShareInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreatePostShare")(required=True)
    share_type = custom_graphql_validator.String.add_option("shareType", "CreatePostShare")()

class CreatePostViewInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreatePostView")(required=True)

class CreateSavedPostInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreateSavedPost")(required=True)

class CreateReviewInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreateReview")(required=True)
    rating = custom_graphql_validator.Int.add_option("rating", "CreateReview")(required=True)
    review_text = custom_graphql_validator.String.add_option("reviewText", "CreateReview")(required=True)

class UpdateReviewInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateReview")(required=True)
    rating = custom_graphql_validator.Int.add_option("rating", "UpdateReview")()
    review_text = custom_graphql_validator.String.add_option("reviewText", "UpdateReview")()

class CreatePinedPostInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "CreatePinedPost")(required=True)

class GetNestedCommentsInput(graphene.InputObjectType):
    post_uid = custom_graphql_validator.String.add_option("postUid", "GetNestedComments")(required=True)
    max_depth = graphene.Int(default_value=3)  # Maximum nesting depth to fetch
    limit = graphene.Int(default_value=10)     # Comments per level
    offset = graphene.Int(default_value=0)

class SendVibeToCommentInput(graphene.InputObjectType):
    comment_uid = custom_graphql_validator.String.add_option("commentUid", "SendVibeToComment")(required=True)
    individual_vibe_id = custom_graphql_validator.String.add_option("individualVibeId", "SendVibeToComment")(required=True)
    vibe_intensity = custom_graphql_validator.Float.add_option("vibeIntensity", "SendVibeToComment")(required=True)