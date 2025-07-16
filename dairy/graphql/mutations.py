import graphene
from graphene import Mutation
from graphql import GraphQLError
from .types import *
from auth_manager.models import Users
from dairy.models import *
from .inputs import *
from .messages import DiaryMessages
from graphql_jwt.decorators import login_required,superuser_required


class CreateTaskCategory(Mutation):
    task_category = graphene.Field(TaskCategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateTaskCategoryInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            task_category = TaskCategory(name=input.name)
            task_category.save()
            task_category.created_by.connect(created_by)

            return CreateTaskCategory(task_category=TaskCategoryType.from_neomodel(task_category), success=True, message=DiaryMessages.TASK_CATEGORY_CREATED)
        except Exception as e:
            return CreateTaskCategory(task_category=None, success=False, message=str(e))




class UpdateTaskCategory(Mutation):
    task_category = graphene.Field(TaskCategoryType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateTaskCategoryInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)

            task_category = TaskCategory.nodes.get(uid=input.uid)

            if input.name is not None:
                task_category.name = input.name

            task_category.save()

            return UpdateTaskCategory(task_category=TaskCategoryType.from_neomodel(task_category), success=True, message=DiaryMessages.TASK_CATEGORY_UPDATED)
        except Exception as e:
            return UpdateTaskCategory(task_category=None, success=False, message=str(e))
        


class DeleteTaskCategory(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteTaskCategoryInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            deleted_by = Users.nodes.get(user_id=user_id)

            task_category = TaskCategory.nodes.get(uid=input.uid)
            task_category.delete()

            return DeleteTaskCategory(success=True, message=DiaryMessages.TASK_CATEGORY_DELETED)
        except Exception as e:
            return DeleteTaskCategory(success=False, message=str(e))


        


class CreateToDo(Mutation):
    todo = graphene.Field(ToDoType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateToDoInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            category = TaskCategory.nodes.get(uid=input.category_uid) if input.category_uid else None

            todo = ToDo(
                title=input.title,
                description=input.description,
                status=input.status,
                time_todo=input.time_todo
            )
            todo.save()
            todo.user.connect(user_node)
            
            category.todo.connect(todo)
            
            user_node.todo.connect(todo)
            if category:
                todo.category.connect(category)

            return CreateToDo(todo=ToDoType.from_neomodel(todo), success=True, message=DiaryMessages.TODO_CREATED)
        except Exception as e:
            return CreateToDo(todo=None, success=False, message=str(e))
        


class UpdateToDo(Mutation):
    todo = graphene.Field(ToDoType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateToDoInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            todo = ToDo.nodes.get(uid=input.uid)

            if input.title is not None:
                todo.title = input.title
            if input.description is not None:
                todo.description = input.description
            if input.status is not None:
                todo.status = input.status
            if input.time_todo is not None:
                todo.time_todo = input.time_todo

            if input.category_uid:
                category = TaskCategory.nodes.get(uid=input.category_uid)
                todo.category.disconnect_all()
                todo.category.connect(category)

            todo.save()

            return UpdateToDo(todo=ToDoType.from_neomodel(todo), success=True, message=DiaryMessages.TODO_UPDATED)
        except Exception as e:
            return UpdateToDo(todo=None, success=False, message=str(e))
        


class DeleteToDo(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteToDoInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            todo = ToDo.nodes.get(uid=input.uid)
            todo.delete()

            return DeleteToDo(success=True, message=DiaryMessages.TODO_DELETED)
        except Exception as e:
            return DeleteToDo(success=False, message=str(e))      
        


class CreateNoteCollection(Mutation):
    note_collection = graphene.Field(NoteCollectionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateNoteCollectionInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            note_collection = NoteCollection(
                name=input.name
            )
            note_collection.save()
            note_collection.created_by.connect(user_node)

            return CreateNoteCollection(note_collection=NoteCollectionType.from_neomodel(note_collection), success=True, message=DiaryMessages.NOTE_COLLECTION_CREATED)
        except Exception as e:
            return CreateNoteCollection(note_collection=None, success=False, message=str(e))       



class UpdateNoteCollection(Mutation):
    note_collection = graphene.Field(NoteCollectionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateNoteCollectionInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            note_collection = NoteCollection.nodes.get(uid=input.uid)

            if input.name is not None:
                note_collection.name = input.name

            note_collection.save()

            return UpdateNoteCollection(note_collection=NoteCollectionType.from_neomodel(note_collection), success=True, message=DiaryMessages.NOTE_COLLECTION_UPDATED)
        except Exception as e:
            return UpdateNoteCollection(note_collection=None, success=False, message=str(e))



class DeleteNoteCollection(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteNoteCollectionInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            note_collection = NoteCollection.nodes.get(uid=input.uid)
            note_collection.delete()

            return DeleteNoteCollection(success=True, message=DiaryMessages.NOTE_COLLECTION_DELETED)
        except Exception as e:
            return DeleteNoteCollection(success=False, message=str(e))



class CreateNote(Mutation):
    note = graphene.Field(NoteType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateNoteInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            collection_node = NoteCollection.nodes.get(uid=input.collection_uid)

            note = Note(
                title=input.title,
                content=input.content
            )
            note.save()
            note.user.connect(user_node)
            collection_node.note.connect(note)
            note.collection.connect(collection_node)
            user_node.note.connect(note)

            return CreateNote(note=NoteType.from_neomodel(note), success=True, message=DiaryMessages.NOTE_CREATED)
        except Exception as e:
            return CreateNote(note=None, success=False, message=str(e))
        


class UpdateNote(Mutation):
    note = graphene.Field(NoteType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateNoteInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            note = Note.nodes.get(uid=input.uid)

            if input.title is not None:
                note.title = input.title

            if input.content is not None:
                note.content = input.content

            note.save()

            return UpdateNote(note=NoteType.from_neomodel(note), success=True, message=DiaryMessages.NOTE_UPDATED)
        except Exception as e:
            return UpdateNote(note=None, success=False, message=str(e))      



class DeleteNote(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteNoteInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            note = Note.nodes.get(uid=input.uid)
            note.delete()

            return DeleteNote(success=True, message=DiaryMessages.NOTE_DELETED)
        except Exception as e:
            return DeleteNote(success=False, message=str(e)) 
        


class CreateReminder(Mutation):
    reminder = graphene.Field(ReminderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateReminderInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            

            reminder = Reminder(
                title=input.title,
                description=input.description,
                date=input.date,
                time=input.time
            )
            reminder.save()
            reminder.user.connect(user_node)
            user_node.reminder.connect(reminder)

            return CreateReminder(reminder=ReminderType.from_neomodel(reminder), success=True, message=DiaryMessages.REMINDER_CREATED)
        except Exception as e:
            return CreateReminder(reminder=None, success=False, message=str(e))      



class UpdateReminder(Mutation):
    reminder = graphene.Field(ReminderType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateReminderInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            reminder = Reminder.nodes.get(uid=input.uid)

            if input.title is not None:
                reminder.title = input.title

            if input.description is not None:
                reminder.description = input.description

            if input.date is not None:
                reminder.date = input.date

            if input.time is not None:
                reminder.time = input.time

            reminder.save()

            return UpdateReminder(reminder=ReminderType.from_neomodel(reminder), success=True, message=DiaryMessages.REMINDER_UPDATED)
        except Exception as e:
            return UpdateReminder(reminder=None, success=False, message=str(e))

class DeleteReminder(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteReminderInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            reminder = Reminder.nodes.get(uid=input.uid)
            reminder.delete()

            return DeleteReminder(success=True, message=DiaryMessages.REMINDER_DELETED)
        except Exception as e:
            return DeleteReminder(success=False, message=str(e))



class CreateMeeting(Mutation):
    meeting = graphene.Field(MeetingType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateMeetingInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by_node = Users.nodes.get(user_id=user_id)
            category_node = TaskCategory.nodes.get(uid=input.category_uid)

            participant_nodes = [Users.nodes.get(uid=uid) for uid in input.participant_uids]

            meeting = Meeting(
                title=input.title,
                description=input.description,
                date=input.date,
                time=input.time
            )
            meeting.save()
            category_node.meeting.connect(meeting)
            meeting.created_by.connect(created_by_node)
            meeting.category.connect(category_node)
            created_by_node.meetings.connect(meeting)
            for participant in participant_nodes:
                meeting.participants.connect(participant)

            return CreateMeeting(meeting=MeetingType.from_neomodel(meeting), success=True, message=DiaryMessages.MEETING_CREATED)
        except Exception as e:
            return CreateMeeting(meeting=None, success=False, message=str(e))



class UpdateMeeting(Mutation):
    meeting = graphene.Field(MeetingType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateMeetingInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            meeting = Meeting.nodes.get(uid=input.uid)

            if input.title is not None:
                meeting.title = input.title

            if input.description is not None:
                meeting.description = input.description

            if input.category_uid is not None:
                category_node = TaskCategory.nodes.get(uid=input.category_uid)
                meeting.category.disconnect_all()
                meeting.category.connect(category_node)

            if input.date is not None:
                meeting.date = input.date

            if input.time is not None:
                meeting.time = input.time

            if input.participant_uids is not None:
                participant_nodes = [Users.nodes.get(uid=uid) for uid in input.participant_uids]
                meeting.participants.disconnect_all()
                for participant in participant_nodes:
                    meeting.participants.connect(participant)

            meeting.save()

            return UpdateMeeting(meeting=MeetingType.from_neomodel(meeting), success=True, message=DiaryMessages.MEETING_UPDATED)
        except Exception as e:
            return UpdateMeeting(meeting=None, success=False, message=str(e))



class DeleteMeeting(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteMeetingInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            meeting = Meeting.nodes.get(uid=input.uid)
            meeting.delete()

            return DeleteMeeting(success=True, message=DiaryMessages.MEETING_DELETED)
        except Exception as e:
            return DeleteMeeting(success=False, message=str(e))

class Mutation(graphene.ObjectType):
    create_task_category=CreateTaskCategory.Field()
    update_task_category=UpdateTaskCategory.Field()
    delete_task_category=DeleteTaskCategory.Field()

    create_todo=CreateToDo.Field()
    update_todo=UpdateToDo.Field()
    delete_todo=DeleteToDo.Field()   

               
    create_note_collection=CreateNoteCollection.Field()
    update_note_collection=UpdateNoteCollection.Field()
    delete_note_collection=DeleteNoteCollection.Field()
    
    create_note=CreateNote.Field()
    update_note=UpdateNote.Field()
    delete_note=DeleteNote.Field()
     
    create_reminder=CreateReminder.Field()
    update_reminder=UpdateReminder.Field()
    delete_reminder=DeleteReminder.Field()

    create_meeting=CreateMeeting.Field()
    update_meeting=UpdateMeeting.Field()
    delete_meeting=DeleteMeeting.Field()
