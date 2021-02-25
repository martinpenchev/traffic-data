from django.urls import path

from .views import (
    repo_list,
    repo_detail,
    home_page
)

app_name = 'users'
urlpatterns = [
    path('users/<str:token>/repos', repo_list, name="user-list"),
    path('users/<str:token>/repos/<int:repository_id>', repo_detail, name="user-detail"),
    path('', home_page, name="home"),
]