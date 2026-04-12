# deploy/api_urls.py
from django.urls import path
from . import api_views

urlpatterns = [
    path('status/', api_views.api_blockchain_status, name='api_blockchain_status'),
    path('validate/', api_views.api_validate_repo, name='api_validate_repo'),
    path('deploy/', api_views.api_deploy_repo, name='api_deploy_repo'),
    path('history/', api_views.api_deployment_history, name='api_deployment_history'),
    path('deployment/<str:deployment_id>/', api_views.api_deployment_details, name='api_deployment_details'),
    path('agents-validate/', api_views.api_agents_validation, name='api_agents_validation'),
    path('block-status/', api_views.api_block_status, name='api_block_status'),
]
