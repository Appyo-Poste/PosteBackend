from django.test import TestCase

from PosteAPI.models import Folder, Post, User
from PosteAPI.serializers import (
    FolderSerializer,
    PostSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserSerializer,
)


class UserSerializerTest(TestCase):
    def test_valid_serializer(self):
        data = {"email": "test@example.com", "username": "test@example.com"}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer(self):
        data = {"email": "invalid_email", "username": "invalid_email"}
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class UserLoginSerializerTest(TestCase):
    def test_valid_login_serializer(self):
        data = {"email": "test@example.com", "password": "securepassword123"}
        serializer = UserLoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_login_serializer(self):
        data = {"email": "invalid_email", "password": "securepassword123"}
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class UserCreateSerializerTest(TestCase):
    def test_valid_create_serializer(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "test@example.com")


class PostSerializerTest(TestCase):
    def test_valid_post_serializer(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        data = {
            "title": "Test Post",
            "description": "Test Description",
            "url": "http://example.com",
            "creator": user.id,
            "folder": folder.id,
        }
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class FolderSerializerTest(TestCase):
    def test_valid_folder_serializer(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        data = {"title": "Test Folder", "creator": user.id}
        serializer = FolderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
