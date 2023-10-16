from django.db.utils import IntegrityError
from django.test import TestCase

from PosteAPI.models import Folder, Post, User, FolderPermissionEnum, FolderPermission


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

    def test_create_folder_via_method(self):
        """
        Previously, we had to call user.create_folder vs. creating the object directly in order to create
        the associated FULL_ACCESS for creator. This has been added to the Folder model's save method, so
        we can now create the object directly -- either way works.
        """
        folder = self.user.create_folder("Test Folder")
        self.assertEqual(folder.title, "Test Folder")
        self.assertEqual(folder.creator, self.user)
        user_folder_permission = FolderPermission.objects.get(
            user=self.user,
            folder=folder
        )
        self.assertEqual(user_folder_permission.permission, FolderPermissionEnum.FULL_ACCESS)

    def test_create_folder(self):
        """
        Replicates behavior of above test without user method
        """
        folder = Folder.objects.create(title="Test Folder", creator=self.user)
        self.assertEqual(folder.title, "Test Folder")
        self.assertEqual(folder.creator, self.user)
        user_folder_permission = FolderPermission.objects.get(
            user=self.user,
            folder=folder
        )
        self.assertEqual(user_folder_permission.permission, FolderPermissionEnum.FULL_ACCESS)


class FolderPermissionModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )
        self.user2 = User.objects.create_user(
            email="test2@example.com", username="another user", password="securepassword123"
        )
        self.folder = self.user.create_folder("Test Folder")

    def test_share_and_unshare_folder(self):
        self.user.share_folder_with_user(self.folder, self.user2, FolderPermissionEnum.EDITOR)
        self.assertTrue(self.user2.can_edit_folder(self.folder))
        self.user.unshare_folder_with_user(self.folder, self.user2)
        self.assertFalse(self.user2.can_edit_folder(self.folder))

    def test_permissions_folder(self):
        self.user3 = User.objects.create_user(
            email="test3@example.com", username="yet another user", password="securepassword123"
        )
        self.user4 = User.objects.create_user(
            email="test4@example.com", username="user four", password="securepassword123"
        )
        self.user.share_folder_with_user(self.folder, self.user2, FolderPermissionEnum.FULL_ACCESS)
        self.user.share_folder_with_user(self.folder, self.user3, FolderPermissionEnum.EDITOR)
        self.user.share_folder_with_user(self.folder, self.user4, FolderPermissionEnum.VIEWER)
        # all users should be able to view
        self.assertTrue(self.user.can_view_folder(self.folder))
        self.assertTrue(self.user2.can_view_folder(self.folder))
        self.assertTrue(self.user3.can_view_folder(self.folder))
        self.assertTrue(self.user4.can_view_folder(self.folder))
        # only editor and above should be able to edit
        self.assertTrue(self.user.can_edit_folder(self.folder))
        self.assertTrue(self.user2.can_edit_folder(self.folder))
        self.assertTrue(self.user3.can_edit_folder(self.folder))
        self.assertFalse(self.user4.can_edit_folder(self.folder))
        # only full_access can share
        self.assertTrue(self.user.can_share_folder(self.folder))
        self.assertTrue(self.user2.can_share_folder(self.folder))
        self.assertFalse(self.user3.can_share_folder(self.folder))
        self.assertFalse(self.user4.can_share_folder(self.folder))
