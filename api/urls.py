from django.urls import path

from .views import (
    UserCreate,
    RepoList,
    RepoCreate,
    RepoDetail,
    RepoDelete
)

app_name = 'api'
urlpatterns = [
    #Users
    path('users/create', UserCreate.as_view(), name="user-create"),

    #Repositories
    path('repos', RepoList.as_view(), name="repo-list"),
    path('repos/create', RepoCreate.as_view(), name="repo-create"),
    path('repos/<int:repository_id>', RepoDetail.as_view(), name="repo-detail"),
    path('repos/<int:repository_id>/delete', RepoDelete.as_view(), name="repo-delete"),
]