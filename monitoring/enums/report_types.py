from enum import Enum
from graphene import Enum as GrapheneEnum

class ReportTypeEnum(Enum):
    USER = 'user'
    COMMUNITY = 'community'
    OTHER = 'other'
    POST = 'post'
    PROFILE = 'profile'

class StatusEnum(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class ReportTypeEnumGQL(GrapheneEnum):
    USER = ReportTypeEnum.USER.value
    COMMUNITY = ReportTypeEnum.COMMUNITY.value
    OTHER = ReportTypeEnum.OTHER.value
    POST = ReportTypeEnum.POST.value
    PROFILE = ReportTypeEnum.PROFILE.value

class StatusEnumGQL(GrapheneEnum):
    PENDING = StatusEnum.PENDING.value
    IN_PROGRESS = StatusEnum.IN_PROGRESS.value
    RESOLVED = StatusEnum.RESOLVED.value
    CLOSED = StatusEnum.CLOSED.value
