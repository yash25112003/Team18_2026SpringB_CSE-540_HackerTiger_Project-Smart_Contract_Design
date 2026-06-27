from django.urls import path
from .views import deploy_from_github_view, home_view

urlpatterns = [
    path("", home_view, name="home"),  # Main interface
    path("deploy/", deploy_from_github_view, name="deploy_from_github"),
]
