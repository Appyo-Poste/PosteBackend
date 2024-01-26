from django.urls import path
from .views import index, folderPage, checkLogin, login_page, landing_page, sign_up, setting, logout_page
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", landing_page, name="landing"),
    path("login/", login_page, name="login"),
    path("folder/", folderPage.as_view(), name="folders"),
    path("loginCheck/", checkLogin, name="login check"),
    path("register/", sign_up, name="register"),
    path("logout/", logout_page, name='logout'),
    path("setting/", setting, name='settings')
]