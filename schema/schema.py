from graphene import Schema
import auth_manager.graphql.schema as auth_manager_schema
import community.graphql.schema as community_schema
import story.graphql.schema as story_schema
import post.graphql.schema as post_schema
import connection.graphql.schema as connection_schema
import msg.graphql.schema as msg_schema
import service.graphql.schema as service_schema
import dairy.graphql.schema as dairy_schema
import shop.graphql.schema as shop_schema
import vibe_manager.graphql.schema as vibe_schema
import job.graphql.schema as job_schema
import monitoring.graphql.schema as monitoring_schema
import agentic.graphql.schema as agentic_schema
from notification.graphql.queries import NotificationQueries
from notification.graphql.mutations import NotificationMutations
from opportunity.graphql.queries import OpportunityQueries
from opportunity.graphql.mutations import OpportunityMutations
from diary.graphql.query import Query as DiaryQuery
from diary.graphql.mutations import Mutation as DiaryMutation

import graphql_jwt

class Query(auth_manager_schema.UserQuery, community_schema.CommunityQuery,story_schema.StoryQuery,post_schema.PostQuery,connection_schema.ConnectionQuery,msg_schema.MsgQuery,service_schema.ServiceQuery,dairy_schema.DairyQuery,shop_schema.ShopQuery,job_schema.JobQuery,vibe_schema.VibeQuery,monitoring_schema.monitoringQuery,agentic_schema.AgentQuery,NotificationQueries,OpportunityQueries,DiaryQuery):
    pass

class Mutation(auth_manager_schema.UserMutation, community_schema.CommunityMutation,story_schema.StoryMutation,post_schema.PostMutation,connection_schema.ConnectionMutation,msg_schema.MsgMutation,service_schema.ServiceMutation,dairy_schema.DairyMutation,shop_schema.ShopMutation,job_schema.JobMutation,vibe_schema.VibeMutation,monitoring_schema.monitoringMutation,agentic_schema.AgentMutation,NotificationMutations,OpportunityMutations,DiaryMutation):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token =graphql_jwt.Revoke.Field()


schema = Schema(query=Query, mutation=Mutation)


