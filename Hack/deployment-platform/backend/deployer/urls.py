# deployer/deployer/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from deploy.views import blockchain_status_view
from django.middleware.csrf import get_token
from django.http import JsonResponse

def redirect_to_deploy(request):
    return redirect('deploy/')

def csrf_token_view(request):
    """API endpoint to get CSRF token"""
    return JsonResponse({'csrfToken': get_token(request)})

urlpatterns = [
    path("", redirect_to_deploy),  # Redirect root to deploy app
    path("admin/", admin.site.urls),
    path("deploy/", include("deploy.urls")),
    path("blockchain/", blockchain_status_view, name="blockchain_status"),
    path("api/", include("deploy.api_urls")),  # API endpoints
    path("api/csrf/", csrf_token_view, name="csrf_token"),  # CSRF token for frontend
]
