from django.urls import path
from .views import index, folderPage, checkLogin, login_page, landing_page, sign_up, setting
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", landing_page, name="landing"),
    path("login/", login_page, name="login"),
    path("folder/", folderPage.as_view(), name="folders"),
    path("loginCheck/", checkLogin, name="login check"),
    path("register/", sign_up, name="register"),
    path("logout/", auth_views.LogoutView.as_view(), name='logout'),
    path("setting/", setting, name='settings')
]