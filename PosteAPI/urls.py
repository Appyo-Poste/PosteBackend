from django.urls import include, path

from .views import (
    UserDetail,
    LoginView,
    DataView,
    FolderAPI,
    PostAPI,
    addPostToFolder,
    deleteFolder,
    FolderForUser,
    FolderDetail,
    UsersView,
)

urlpatterns = [
    path("users/", UsersView.as_view(), name="users-list"),  # GET to retrieve users, POST to create a user
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("login/", LoginView.as_view(), name="user-login"),  # POST to login
    path("data/", DataView.as_view(), name="user-folders"),  # GET to retrieve folders and posts to update client
    path("data/folder/", DataView.as_view(), name="folder"),  # UPDATE user permissions
    path("data/folder/<int:pk>", FolderDetail.as_view(), name="specific-folder"),  # GET specific folder
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("folders/", FolderAPI.as_view(), name="folders-list"),
    path("folders/user/<int:pk>",FolderForUser.as_view()),
    path("posts/", PostAPI.as_view(), name="post-lists"),
    path("posts/addToFolder/<int:pk>&<int:pk2>", addPostToFolder.as_view(), name="add a post to a folder"),
    path("folders/deleteFolder/<int:pk>/", deleteFolder.as_view(), name="delete a folder"),
]
