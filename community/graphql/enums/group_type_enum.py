
import graphene
class GroupTypeEnum(graphene.Enum):
    PERSONAL_GROUP = "personal group"
    INTEREST_GROUP = "interest group"
    OFFICIAL_GROUP = "official group"
    BUSINESS_GROUP = "business group"


class CategoryEnum(graphene.Enum):
    PUBLIC = "public"
    PRIVATE = "private"