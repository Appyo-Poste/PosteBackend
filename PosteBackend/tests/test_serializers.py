from django.test import TestCase

from PosteAPI.models import Folder, Post, User
from PosteAPI.serializers import (
    FolderSerializer,
    PostSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserSerializer,
    FolderCreateSerializer,
    PostCreateSerializer,
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
    def test_valid_create_serializer_first_and_last(self):
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
        self.assertNotEquals(user.password, "securepassword123")

    def test_valid_create_serializer_name_only(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertNotEquals(user.password, "securepassword123")

    def test_valid_create_serializer_name_and_first_name(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "first_name": "Something",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertNotEquals(user.password, "securepassword123")

    def test_valid_create_serializer_name_and_last_name(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "last_name": "Something",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertNotEquals(user.password, "securepassword123")

    def test_valid_create_serializer_all_names(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User",
            "first_name": "Something",
            "last_name": "Else",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "Something")
        self.assertEqual(user.last_name, "Else")
        self.assertNotEquals(user.password, "securepassword123")

    def test_serializer_fails_no_names(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_serializer_fails_last_name_only(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "last_name": "Else",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_name_without_space(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "TestUser",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "TestUser")
        self.assertEqual(user.last_name, "")

    def test_name_with_many_spaces(self):
        data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "name": "Test User Has Many Names",
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User Has Many Names")


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


class FolderCreateSerializerTest(TestCase):
    def test_valid_folder(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        data = {
            "title": "test folder",
            "creator": user.id,
        }
        serializer = FolderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_title(self):
        data = {
            "title": "",
        }
        serializer = FolderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class PostCreateSerializerTest(TestCase):
    def test_valid_post(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        data = {
            "title": "Test Post",
            "description": "Test Description",
            "url": "http://example.com",
            "folder_id": folder.id,
        }
        serializer = PostCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_name(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        data = {
            "title": "",
            "description": "Test Description",
            "url": "http://example.com",
            "creator": user.id,
            "folder": folder.id,
        }

        serializer = PostCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_url(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        data = {
            "title": "Test Post",
            "description": "Test Description",
            "url": "http://example",
            "creator": user.id,
            "folder": folder.id,
        }

        serializer = PostCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_user(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        data = {
            "title": "Test Post",
            "description": "Test Description",
            "url": "http://example.com",
            "creator": 2,
            "folder": folder.id,
        }

        serializer = PostCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_folder(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        data = {
            "title": "Test Post",
            "description": "Test Description",
            "url": "http://example.com",
            "creator": user.id,
            "folder": 2,
        }

        serializer = PostCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())