from django.urls import path
from .views import index, folderPage, checkLogin

urlpatterns = [
    path("", index, name="index"),
    path("test/", folderPage.as_view(), name="folders"),
    path("loginCheck/", checkLogin, name="login check"),
]