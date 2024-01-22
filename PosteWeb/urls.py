from django.urls import path
from .views import index, folderPage, checkLogin, login_page, landing_page, sign_up

urlpatterns = [
    path("", landing_page, name="landing"),
    path("login/", login_page, name="login"),
    path("folder/", folderPage.as_view(), name="folders"),
    path("loginCheck/", checkLogin, name="login check"),
    path("register/", sign_up.as_view(), name="register"),
]