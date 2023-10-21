from django.urls import include, path

from .views import UsersView, UserDetail, LoginView, DataView, FolderDetail

urlpatterns = [
    path("users/", UsersView.as_view(), name="user-list"),  # GET to list users, POST to create a user
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("login/", LoginView.as_view(), name="user-login"),  # POST to login
    path("data/", DataView.as_view(), name="user-folders"),  # GET to retrieve folders and posts to update client
    path("data/folder/", DataView.as_view(), name="folder"),  # UPDATE user permissions
    path("data/folder/<int:pk>", FolderDetail.as_view(), name="specific-folder"),  # GET specific folder
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
