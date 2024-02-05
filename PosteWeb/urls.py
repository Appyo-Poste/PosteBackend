from django.urls import path
from .views import index, folderPage, checkLogin, login_page, landing_page, sign_up, setting, logout_page, folder_create, postPage, post_create
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", landing_page, name="landing"),
    path("login/", login_page, name="login"),
    path("folder/", folderPage.as_view(), name="folders"),
    path("loginCheck/", checkLogin, name="login check"),
    path("register/", sign_up, name="register"),
    path("logout/", logout_page, name='logout'),
    path("setting/", setting, name='settings'),
    path("newFolder/", folder_create,  name='newFolder'),
    path("contents/<int:pk>/", postPage.as_view(), name="contents"),
    path("newPost/", post_create, name="newPost")
]