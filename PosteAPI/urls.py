from django.urls import include, path, re_path

from .views import UserAPI, UserDetail, UserLogin, FolderAPI, FolderForUser

urlpatterns = [
    # GET to list users, POST to create a user
    path("users/", UserAPI.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("login/", UserLogin.as_view(), name="user-login"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("folders/", FolderAPI.as_view(), name="folders-list"),
    path("folders/user/<int:name>/", FolderForUser.as_view(), name="user-folders"),
]
