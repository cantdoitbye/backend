import graphene

class CreateTaskCategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)

class UpdateTaskCategoryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()

class DeleteTaskCategoryInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateToDoInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String()
    category_uid = graphene.String(required=True)
    status = graphene.Boolean()
    time_todo = graphene.DateTime()

class UpdateToDoInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    title = graphene.String()
    description = graphene.String()
    category_uid = graphene.String()
    status = graphene.Boolean()
    time_todo = graphene.DateTime()

class DeleteToDoInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateNoteCollectionInput(graphene.InputObjectType):
    name = graphene.String(required=True)

class UpdateNoteCollectionInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = graphene.String()

class DeleteNoteCollectionInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateNoteInput(graphene.InputObjectType):
    collection_uid = graphene.String(required=True)
    title = graphene.String(required=True)
    content = graphene.String(required=True)

class UpdateNoteInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    title = graphene.String()
    content = graphene.String()

class DeleteNoteInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateReminderInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    date = graphene.Date(required=True)
    time = graphene.DateTime(required=True)

class UpdateReminderInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    title = graphene.String()
    description = graphene.String()
    date = graphene.Date()
    time = graphene.DateTime()

class DeleteReminderInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateMeetingInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    category_uid = graphene.String(required=True)
    date = graphene.Date(required=True)
    time = graphene.DateTime(required=True)
    participant_uids = graphene.List(graphene.String, required=True)

class UpdateMeetingInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    title = graphene.String()
    description = graphene.String()
    category_uid = graphene.String()
    date = graphene.Date()
    time = graphene.DateTime()
    participant_uids = graphene.List(graphene.String)

class DeleteMeetingInput(graphene.InputObjectType):
    uid = graphene.String(required=True)