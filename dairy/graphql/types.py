import graphene
from graphene import ObjectType

from auth_manager.graphql.types import UserType


class TaskCategoryType(ObjectType):
    uid = graphene.String()
    name = graphene.String()
    created_on = graphene.DateTime()
    created_by = graphene.Field(UserType)
    todo=graphene.List(lambda:ToDoNonCategoryType)
    meeting= graphene.List(lambda:MeetingNonCategoryType)
    @classmethod
    def from_neomodel(cls, task_category):
        return cls(
            uid=task_category.uid,
            name=task_category.name,
            created_on=task_category.created_on,
            created_by=UserType.from_neomodel(task_category.created_by.single()) if task_category.created_by.single() else None,
            todo=[ToDoNonCategoryType.from_neomodel(x) for x in task_category.todo],
            meeting=[MeetingNonCategoryType.from_neomodel(x) for x in task_category.meeting],
        )

class ToDoType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    title = graphene.String()
    description = graphene.String()
    category = graphene.Field(TaskCategoryType)
    status = graphene.Boolean()
    time_todo = graphene.DateTime()
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, todo):
        return cls(
            uid=todo.uid,
            user=UserType.from_neomodel(todo.user.single()) if todo.user.single() else None,
            title=todo.title,
            description=todo.description,
            category=TaskCategoryType.from_neomodel(todo.category.single()) if todo.category.single() else None,
            status=todo.status,
            time_todo=todo.time_todo,
            created_on=todo.created_on
        )
class ToDoNonCategoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    title = graphene.String()
    description = graphene.String()
    status = graphene.Boolean()
    time_todo = graphene.DateTime()
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, todo):
        return cls(
            uid=todo.uid,
            user=UserType.from_neomodel(todo.user.single()) if todo.user.single() else None,
            title=todo.title,
            description=todo.description,
            status=todo.status,
            time_todo=todo.time_todo,
            created_on=todo.created_on
        )

class NoteCollectionType(ObjectType):
    uid = graphene.String()
    created_by = graphene.Field(UserType)
    name = graphene.String()
    created_on = graphene.DateTime()
    note=graphene.List(lambda:NoteNoCollectionType)
    @classmethod
    def from_neomodel(cls, note_collection):
        return cls(
            uid=note_collection.uid,
            created_by=UserType.from_neomodel(note_collection.created_by.single()) if note_collection.created_by.single() else None,
            name=note_collection.name,
            created_on=note_collection.created_on,
            note=[NoteNoCollectionType.from_neomodel(x) for x in note_collection.note],
        )
    
class NoteType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    collection = graphene.Field(NoteCollectionType)
    title = graphene.String()
    content = graphene.String()
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, note):
        return cls(
            uid=note.uid,
            user=UserType.from_neomodel(note.user.single()) if note.user.single() else None,
            collection=NoteCollectionType.from_neomodel(note.collection.single()) if note.collection.single() else None,
            title=note.title,
            content=note.content,
            created_on=note.created_on
        )
    
class ReminderType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    title = graphene.String()
    description = graphene.String()
    date = graphene.Date()
    time = graphene.DateTime()
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, reminder):
        return cls(
            uid=reminder.uid,
            user=UserType.from_neomodel(reminder.user.single()) if reminder.user.single() else None,
            title=reminder.title,
            description=reminder.description,
            date=reminder.date,
            time=reminder.time,
            created_on=reminder.created_on
        )
    
class MeetingType(ObjectType):
    uid = graphene.String()
    created_by = graphene.Field(UserType)
    title = graphene.String()
    description = graphene.String()
    category = graphene.Field(TaskCategoryType)
    date = graphene.Date()
    time = graphene.DateTime()
    participants = graphene.List(UserType)
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, meeting):
        return cls(
            uid=meeting.uid,
            created_by=UserType.from_neomodel(meeting.created_by.single()) if meeting.created_by.single() else None,
            title=meeting.title,
            description=meeting.description,
            category=TaskCategoryType.from_neomodel(meeting.category.single()) if meeting.category.single() else None,
            date=meeting.date,
            time=meeting.time,
            participants=[UserType.from_neomodel(user) for user in meeting.participants.all()],
            created_on=meeting.created_on
        )
    
class ToDoNonCategoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    title = graphene.String()
    description = graphene.String()
    status = graphene.Boolean()
    time_todo = graphene.DateTime()
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, todo):
        return cls(
            uid=todo.uid,
            user=UserType.from_neomodel(todo.user.single()) if todo.user.single() else None,
            title=todo.title,
            description=todo.description,
            status=todo.status,
            time_todo=todo.time_todo,
            created_on=todo.created_on
        )
    
class NoteNoCollectionType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    title = graphene.String()
    content = graphene.String()
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, note):
        return cls(
            uid=note.uid,
            user=UserType.from_neomodel(note.user.single()) if note.user.single() else None,
            title=note.title,
            content=note.content,
            created_on=note.created_on
        )
    
class MeetingNonCategoryType(ObjectType):
    uid = graphene.String()
    created_by = graphene.Field(UserType)
    title = graphene.String()
    description = graphene.String()
    date = graphene.Date()
    time = graphene.DateTime()
    participants = graphene.List(UserType)
    created_on = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, meeting):
        return cls(
            uid=meeting.uid,
            created_by=UserType.from_neomodel(meeting.created_by.single()) if meeting.created_by.single() else None,
            title=meeting.title,
            description=meeting.description,
            date=meeting.date,
            time=meeting.time,
            participants=[UserType.from_neomodel(user) for user in meeting.participants.all()],
            created_on=meeting.created_on
        )