from django.urls import path
from .views import (index, folderPage, login_page, landing_page, sign_up, setting, logout_page, folder_create,
                    postPage, post_create, deleteFolder, folder_share, FolderShares, delete_share, delete_post)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", landing_page, name="landing"),
    path("login/", login_page, name="login"),
    path("folder/", folderPage.as_view(), name="folders"),
    path("register/", sign_up, name="register"),
    path("logout/", logout_page, name='logout'),
    path("setting/", setting, name='settings'),
    path("newFolder/", folder_create,  name='newFolder'),
    path("contents/<int:pk>/", postPage.as_view(), name="contents"),
    path("newPost/", post_create, name="newPost"),
    path("deleteFolder/<int:pk>/", deleteFolder, name="deleteFolder"),
    path("share/<int:pk>", folder_share, name="share"),
    path("share/edit/<int:pk>", FolderShares.as_view(), name="shareEdit"),
    path("share/delete/<int:pk>&<int:uid>", delete_share, name="unshare"),
    path("delete/post/<int:pk>&<int:pid>", delete_post, name="delete_post")
]
