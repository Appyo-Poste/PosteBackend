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
    UsersView,
    DeletePostView,
)

urlpatterns = [
    # GET to retrieve users, POST to create a user
    path("users/", UsersView.as_view(), name="users-list"),

    # GET to retrieve user details
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),

    # POST to login
    path("login/", LoginView.as_view(), name="user-login"),

    # GET to retrieve data: folders and posts to update client
    path("data/", DataView.as_view(), name="user-folders"),

    # GET to list all folder, POST to create a folder
    path("folders/", FolderAPI.as_view(), name="folders-list"),

    # GET to list all folders for a user
    path("folders/user/<int:pk>",FolderForUser.as_view()),

    # GET to list all posts
    # POST to create a post
    # DELETE to delete a post
    # PATCH to edit a post
    path("posts/", PostAPI.as_view(), name="post-lists"),

    path("posts/<int:id>/", DeletePostView.as_view(), name="delete-post"),

    # GET to add a post to a folder (should refactor to POST)
    path("posts/addToFolder/<int:pk>&<int:pk2>", addPostToFolder.as_view(), name="add a post to a folder"),

    # GET to delete a folder (should refactor to DELETE)
    path("folders/deleteFolder/<int:pk>/", deleteFolder.as_view(), name="delete a folder"),

    # Authentication; not used in client
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

