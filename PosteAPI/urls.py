from django.urls import include, path, re_path

from .views import UserAPI, UserDetail, UserLogin, FolderAPI, FolderForUser, PostAPI, addPostToFolder, deleteFolder

urlpatterns = [
    # GET to list users, POST to create a user
    path("users/", UserAPI.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("login/", UserLogin.as_view(), name="user-login"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("folders/", FolderAPI.as_view(), name="folders-list"),
    path("folders/user/<int:pk>/", FolderForUser.as_view(), name="user-folders"),
    path("posts/", PostAPI.as_view(), name="post-lists"),
    path("posts/addToFolder/<int:pk>&<int:pk2>", addPostToFolder.as_view(), name="add a post to a folder"),
    path("folders/deleteFolder/<int:pk>/", deleteFolder.as_view(), name="delete a folder"),
]
