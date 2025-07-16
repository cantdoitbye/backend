import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required,superuser_required

from .types import *
from auth_manager.models import Users
from dairy.models import *

class Query(graphene.ObjectType):

    all_task_categories = graphene.List(TaskCategoryType)
    @login_required
    def resolve_all_task_categories(self, info):
        return [TaskCategoryType.from_neomodel(tc) for tc in TaskCategory.nodes.all()] 

    task_category_by_uid = graphene.Field(TaskCategoryType, uid=graphene.String(required=True))
    @login_required
    def resolve_task_category_by_uid(self, info, uid):
        try:
            task_category = TaskCategory.nodes.get(uid=uid)
            return TaskCategoryType.from_neomodel(task_category)
        except TaskCategory.DoesNotExist:
            return None
        
    all_todos = graphene.List(ToDoType)
    @login_required
    def resolve_all_todos(self, info):
        return [ToDoType.from_neomodel(todo) for todo in ToDo.nodes.all()]
        
    todo_by_uid = graphene.Field(ToDoType, uid=graphene.String(required=True))
    @login_required
    def resolve_todo_by_uid(self, info, uid):
        try:
            todo = ToDo.nodes.get(uid=uid)
            return ToDoType.from_neomodel(todo)
        except ToDo.DoesNotExist:
            return None
        
    all_note_collections = graphene.List(NoteCollectionType)
    @login_required
    def resolve_all_note_collections(self, info):
        return [NoteCollectionType.from_neomodel(note_collection) for note_collection in NoteCollection.nodes.all()]
    
    note_collection_by_uid = graphene.Field(NoteCollectionType, uid=graphene.String(required=True))
    @login_required
    def resolve_note_collection_by_uid(self, info, uid):
        try:
            note_collection = NoteCollection.nodes.get(uid=uid)
            return NoteCollectionType.from_neomodel(note_collection)
        except NoteCollection.DoesNotExist:
            return None
        
    all_notes = graphene.List(NoteType)
    @login_required
    def resolve_all_notes(self, info):
        return [NoteType.from_neomodel(note) for note in Note.nodes.all()]
    
    note_by_uid = graphene.Field(NoteType, uid=graphene.String(required=True))
    @login_required
    def resolve_note_by_uid(self, info, uid):
        try:
            note = Note.nodes.get(uid=uid)
            return NoteType.from_neomodel(note)
        except Note.DoesNotExist:
            return None

    my_note=graphene.List(NoteType)

    @login_required
    def resolve_my_note(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            
            my_notes=list(user_node.note.all())

            return [NoteType.from_neomodel(x) for x in my_notes]
        except Exception as e:
            raise Exception(e)


    all_reminders = graphene.List(ReminderType)
    @login_required
    def resolve_all_reminders(self, info):
        return [ReminderType.from_neomodel(reminder) for reminder in Reminder.nodes.all()]
    
    reminder_by_uid = graphene.Field(ReminderType, uid=graphene.String(required=True))
    @login_required
    def resolve_reminder_by_uid(self, info, uid):
        try:
            reminder = Reminder.nodes.get(uid=uid)
            return ReminderType.from_neomodel(reminder)
        except Reminder.DoesNotExist:
            return None

    my_reminder=graphene.List(ReminderType)

    @login_required
    def resolve_my_reminder(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            
            my_reminders=list(user_node.reminder.all())

            return [ReminderType.from_neomodel(x) for x in my_reminders]
        except Exception as e:
            raise Exception(e) 

    all_meetings = graphene.List(MeetingType)
    @login_required
    def resolve_all_meetings(self, info):
        return [MeetingType.from_neomodel(meeting) for meeting in Meeting.nodes.all()]
    
    meeting_by_uid = graphene.Field(MeetingType, uid=graphene.String(required=True))
    @login_required
    def resolve_meeting_by_uid(self, info, uid):
        try:
            meeting = Meeting.nodes.get(uid=uid)
            return MeetingType.from_neomodel(meeting)
        except Meeting.DoesNotExist:
            return None
        
    my_meeting=graphene.List(MeetingType)

    @login_required
    def resolve_my_meeting(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            
            my_meetings=list(user_node.meetings.all())

            return [MeetingType.from_neomodel(meeting) for meeting in my_meetings]
        except Exception as e:
            raise Exception(e)

