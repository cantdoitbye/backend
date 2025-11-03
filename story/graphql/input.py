import graphene
from story.graphql.enum.circle_type import CircleStoryTypeEnum
from auth_manager.validators import custom_graphql_validator


class CreateStoryInput(graphene.InputObjectType):
    """Input fields required to create a new story."""
    title = custom_graphql_validator.SpecialCharacterString2_200.add_option("title", "CreateStory")( desc="The title of the story to display.")
    content = custom_graphql_validator.SpecialCharacterString2_100.add_option("content", "CreateStory")(desc="The main content or body of the story.")
    captions = custom_graphql_validator.SpecialCharacterString2_200.add_option("captions", "CreateStory")(desc="A brief caption or tagline for the story.")
    privacy = custom_graphql_validator.ListString.add_option("privacy", "CreateStory")(desc="Privacy level of the story, determining visibility.", required=True)
    story_image_id = custom_graphql_validator.String.add_option("storyImageId", "CreateStory")(desc="ID of the image associated with the story.")
    mentioned_user_uids = graphene.List(graphene.String)

class UpdateStoryInput(graphene.InputObjectType):
    """Input fields required to update an existing story."""
    uid = custom_graphql_validator.String.add_option("uid", "UpdateStory")(required=True, desc="Unique identifier of the story to update.")
    captions = custom_graphql_validator.NonSpecialCharacterString10_200.add_option("captions", "UpdateStory")(desc="A brief caption or tagline for the story.")

class DeleteInput(graphene.InputObjectType):
    """Input field required to delete an entity by UID."""
    uid = custom_graphql_validator.String.add_option("uid", "Delete")(required=True, desc="Unique identifier of the entity to delete.")



class StoryCommentInput(graphene.InputObjectType):
    story_uid = custom_graphql_validator.String.add_option("storyUid", "CreateStoryComment")(required=True)
    content = custom_graphql_validator.NonSpecialCharacterString1_200.add_option("content", "CreateStoryComment")(required=True)

class UpdateStoryCommentInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateStoryComment")(required=True)
    content = custom_graphql_validator.NonSpecialCharacterString1_200.add_option("content", "UpdateStoryComment")(required=True)

class StoryReactionInput(graphene.InputObjectType):
    story_uid = custom_graphql_validator.String.add_option("storyUid", "CreateStoryReaction")(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateStoryReaction")(default_value='Like')
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateStoryReaction")(default_value=2.0)

class UpdateStoryReactionInput(graphene.InputObjectType):
    uid=custom_graphql_validator.String.add_option("uid", "UpdateStoryReaction")(required=True)
    reaction=custom_graphql_validator.String.add_option("reaction", "UpdateStoryReaction")()
    vibe=custom_graphql_validator.Float.add_option("vibe", "UpdateStoryReaction")()


class StoryRatingInput(graphene.InputObjectType):
    story_uid = custom_graphql_validator.String.add_option("storyUid", "StoryRating")(required=True)
    rating = custom_graphql_validator.Int.add_option("rating", "StoryRating")(default_value=1)

class UpdateStoryRatingInput(graphene.InputObjectType):
    uid=custom_graphql_validator.String.add_option("uid", "UpdateStoryRating")(required=True)
    rating=custom_graphql_validator.Int.add_option("rating", "UpdateStoryRating")()

class ViewStoryInput(graphene.InputObjectType):
    story_uid = custom_graphql_validator.String.add_option("storyUid", "ViewStory")(required=True)
    

class ShareStoryInput(graphene.InputObjectType):
    story_uid = custom_graphql_validator.String.add_option("storyUid", "ShareStory")(required=True)
    share_type=custom_graphql_validator.String.add_option("shareType", "ShareStory")()