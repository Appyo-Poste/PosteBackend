from django.test import TestCase

from PosteAPI.models import Folder, Post, User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create(
            email="test@example.com", password="securepassword123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "test@example.com")


class PostModelTest(TestCase):
    def test_create_post(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        post = Post.objects.create(
            title="Test Post",
            description="Test Description",
            url="http://example.com",
            creator=user,
            folder=folder,
        )
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.description, "Test Description")


class FolderModelTest(TestCase):
    def test_create_folder(self):
        user = User.objects.create(
            email="creator@example.com", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=user)
        self.assertEqual(folder.title, "Test Folder")
