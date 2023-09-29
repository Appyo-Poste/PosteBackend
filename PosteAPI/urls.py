from django.urls import include, path, re_path

from .views import UserCreate, UserDetail, UserList, UserLogin

urlpatterns = [
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("login/", UserLogin.as_view(), name="user-login"),
    path("create/", UserCreate.as_view(), name="user-create"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
