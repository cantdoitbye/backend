from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from django.contrib import admin
from django.urls import path,include
from django.shortcuts import redirect
from schema import schema, schemaV2
from auth_manager.views import CustomGraphQLView
from docs.views import docs_home, api_reference, integration_guide




urlpatterns = [
    path('admin/', admin.site.urls),
    # path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),  # Version 1
    path('graphql/v2/', csrf_exempt(CustomGraphQLView.as_view(graphiql=True, schema=schemaV2))),  # Version 2
    path('', lambda request: redirect('/docs/')),
    path('docs/', docs_home, name='docs_home'),
    path('docs/reference/', api_reference, name='api_reference'),
    path('docs/guide/', integration_guide, name='integration_guide'),


    path('', include('upload.urls')),

]
