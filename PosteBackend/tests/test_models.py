from django.db.utils import IntegrityError
from django.test import TestCase

from PosteAPI.models import Folder, Post, User


class UserModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )

    def test_create_user(self):
        self.assertEqual(self.user.email, "test@example.com")
        # We are setting username to email, as we are using email as primary identifier
        self.assertEqual(self.user.username, "test@example.com")
        # Should fail due to password hashing
        self.assertNotEquals(self.user.password, "securepassword123")
        # Should pass due to Django checking hashed password
        self.assertTrue(self.user.check_password("securepassword123"))
        # Should fail due to unique constraint
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="test@example.com",
                username="unused",
                password="securepassword123",
            )


class PostModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )

    def test_create_post(self):
        folder = Folder.objects.create(title="Test Folder", creator=self.user)
        post = Post.objects.create(
            title="Test Post",
            description="Test Description",
            url="http://example.com",
            creator=self.user,
            folder=folder,
        )
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.description, "Test Description")
        self.assertEqual(post.url, "http://example.com")
        self.assertEqual(post.creator, self.user)
        self.assertEqual(post.folder, folder)


class FolderModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )

    def test_create_folder(self):
        folder = Folder.objects.create(title="Test Folder", creator=self.user)
        self.assertEqual(folder.title, "Test Folder")
        self.assertEqual(folder.creator, self.user)

    def test_share_folder(self):
        user2 = User.objects.create_user(
            email="user2@email.com", username="unused", password="securepassword123"
        )
        folder = Folder.objects.create(title="Test Folder", creator=self.user)
        folder.shared_users.add(user2)
        self.assertEqual(folder.shared_users.count(), 1)
        self.assertEqual(folder.shared_users.first(), user2)
        self.assertEqual(user2.shared_folders.count(), 1)
        self.assertEqual(user2.shared_folders.first(), folder)
