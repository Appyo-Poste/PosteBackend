from django.urls import include, path

from .views import (
    AddPostToFolder,
    ChangePassword,
    DataView,
    FolderAPI,
    FolderDetail,
    FolderForUser,
    IndividualPostView,
    LoginView,
    PostAPI,
    UserDetail,
    UsersView,
    deleteFolder,
)

urlpatterns = [
    # GET to retrieve users
    # POST to create a user
    path("users/", UsersView.as_view(), name="users-list"),
    # GET to retrieve user details
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    # POST to change user's password
    path("users/changepassword/", ChangePassword.as_view(), name="change-password"),
    # POST to login
    path("login/", LoginView.as_view(), name="user-login"),
    # GET to retrieve root folder details: folders, posts, and shared folders
    path("data/", DataView.as_view(), name="get-root-data"),
    # GET to retrieve specific folder details: folders, posts (but not shared folders)
    path("data/<int:folder_id>/", DataView.as_view(), name="get-folder-data"),
    # POST to update user permissions
    path("data/folder/", DataView.as_view(), name="folder"),
    # GET specific folder
    # PATCH to update title for specific folder
    path("data/folder/<int:pk>/", FolderDetail.as_view(), name="specific-folder"),
    # GET to list all folder, POST to create a folder
    path("folders/", FolderAPI.as_view(), name="folders-list"),
    # DELETE to delete a folder
    path("folders/<int:pk>/", deleteFolder.as_view(), name="delete a folder"),
    # GET to list all folders for a user
    path("folders/user/<int:pk>/", FolderForUser.as_view()),
    # GET to list all posts
    # POST to create a post
    path("posts/", PostAPI.as_view(), name="post-lists"),
    # DELETE to delete a post
    # PATCH to edit a post
    path("posts/<int:id>/", IndividualPostView.as_view(), name="post-detail"),
    # GET to add a post to a folder (should refactor to POST)
    path(
        "posts/addToFolder/<int:pk>&<int:pk2>/",
        AddPostToFolder.as_view(),
        name="add a post to a folder",
    ),
    # Authentication; not used in client
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
