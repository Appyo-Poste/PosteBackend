from django.urls import path
from .views import index, folderPage, checkLogin, login_page

urlpatterns = [
    path("", login_page, name="login"),
    path("folder/", folderPage.as_view(), name="folders"),
    path("loginCheck/", checkLogin, name="login check"),
]