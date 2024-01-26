from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from PosteAPI.models import (
    Folder,
    FolderPermission,
    FolderPermissionEnum,
    Post,
    Tag,
    User,
)


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
        self.assertTrue(self.user.can_edit_folder(folder))
        self.assertTrue(self.user.can_share_folder(folder))

    def test_create_folder(self):
        """
        Replicates behavior of above test without user method
        """
        folder = Folder.objects.create(title="Test Folder", creator=self.user)
        self.assertEqual(folder.title, "Test Folder")
        self.assertEqual(folder.creator, self.user)
        self.assertTrue(self.user.can_edit_folder(folder))
        self.assertTrue(self.user.can_share_folder(folder))


class FolderPermissionModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )
        self.user2 = User.objects.create_user(
            email="test2@example.com",
            username="another user",
            password="securepassword123",
        )
        self.folder = self.user.create_folder("Test Folder")

    def test_share_and_unshare_folder(self):
        self.user.share_folder_with_user(
            self.folder, self.user2, FolderPermissionEnum.EDITOR
        )
        self.assertTrue(self.user2.can_edit_folder(self.folder))
        self.user.unshare_folder_with_user(self.folder, self.user2)
        self.assertFalse(self.user2.can_edit_folder(self.folder))

    def test_permissions_folder(self):
        self.user3 = User.objects.create_user(
            email="test3@example.com",
            username="yet another user",
            password="securepassword123",
        )
        self.user4 = User.objects.create_user(
            email="test4@example.com",
            username="user four",
            password="securepassword123",
        )
        self.user.share_folder_with_user(
            self.folder, self.user2, FolderPermissionEnum.FULL_ACCESS
        )
        self.user.share_folder_with_user(
            self.folder, self.user3, FolderPermissionEnum.EDITOR
        )
        self.user.share_folder_with_user(
            self.folder, self.user4, FolderPermissionEnum.VIEWER
        )
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


class FolderNestedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )
        self.folder1 = self.user.create_folder("Folder 1")
        self.folder2 = self.user.create_folder("Folder 2")
        self.folder3 = self.user.create_folder("Folder 3")
        self.folder4 = self.user.create_folder("Folder 4")
        self.folder5 = self.user.create_folder("Folder 5")

    def test_new_folders_have_no_parent(self):
        self.assertIsNone(self.folder1.parent)
        self.assertIsNone(self.folder2.parent)
        self.assertIsNone(self.folder3.parent)
        self.assertIsNone(self.folder4.parent)
        self.assertIsNone(self.folder5.parent)

    def test_can_set_folder_parent(self):
        self.folder2.set_parent(self.folder1)
        self.assertEqual(self.folder2.parent, self.folder1)

    def test_cannot_set_self_as_parent(self):
        with self.assertRaises(ValidationError):
            self.folder1.set_parent(self.folder1)

    def test_can_create_chain(self):
        self.folder5.set_parent(self.folder4)
        self.folder4.set_parent(self.folder3)
        self.folder3.set_parent(self.folder2)
        self.folder2.set_parent(self.folder1)
        self.assertEqual(self.folder5.parent, self.folder4)
        self.assertEqual(self.folder4.parent, self.folder3)
        self.assertEqual(self.folder3.parent, self.folder2)
        self.assertEqual(self.folder2.parent, self.folder1)
        self.assertEqual(self.folder1.parent, None)

    def test_cannot_set_parent_in_descendants(self):
        self.folder5.set_parent(self.folder4)
        self.folder4.set_parent(self.folder3)
        self.folder3.set_parent(self.folder2)
        self.folder2.set_parent(self.folder1)
        with self.assertRaises(ValidationError):
            self.folder2.set_parent(self.folder5)
        with self.assertRaises(ValidationError):
            self.folder2.set_parent(self.folder4)
        with self.assertRaises(ValidationError):
            self.folder2.set_parent(self.folder3)

    def test_can_change_root_of_ancestry(self):
        self.folder4.set_parent(self.folder3)
        self.folder3.set_parent(self.folder2)
        self.folder2.set_parent(self.folder1)
        self.folder5.set_parent(self.folder1)
        self.folder4.set_parent(self.folder5)
        self.folder2.set_parent(self.folder5)
        self.assertEqual(self.folder2.parent, self.folder5)
        self.assertEqual(self.folder3.parent, self.folder2)
        self.assertEqual(self.folder4.parent, self.folder5)
        self.assertEqual(self.folder5.parent, self.folder1)


class TagModelTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", username="unused", password="securepassword123"
        )
        self.folder = self.user.create_folder("Test Folder")

    def test_add_tag_to_post(self):
        # Create a post without tags
        post = Post.objects.create(
            title="Sample Post",
            description="Sample description",
            url="http://example.com",
            creator=self.user,
            folder=self.folder,
        )

        # Create a tag and add it to the post
        tag = Tag.objects.create(name="test")
        post.tags.add(tag)
        post.save()

        # Retrieve the post again and confirm it has one tag
        post_with_tag = Post.objects.get(id=post.id)
        self.assertEqual(post_with_tag.tags.count(), 1)
        self.assertIn(tag, post_with_tag.tags.all())

    def test_tags_stored_in_lowercase(self):
        # Create a tag with uppercase letters
        Tag.objects.create(name="TEST")

        # Check if the tag was converted to lowercase
        tag = Tag.objects.get(name="test")
        self.assertEqual(tag.name, "test")

        # Attempt to create another tag with the same name but different case
        try:
            with transaction.atomic():
                Tag.objects.create(name="tEsT")
            self.fail(
                "Creating a tag with the same name but different casing did not raise an IntegrityError."
            )
        except IntegrityError:
            # This is expected, so the test should pass
            pass

        # Confirm that no additional tag has been added
        self.assertEqual(Tag.objects.count(), 1)

    def test_tag_str(self):
        tag = Tag.objects.create(name="test")
        self.assertEqual(str(tag), "test")

    def test_tag_unique(self):
        Tag.objects.create(name="test")
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="TEST")

    def test_tag_strips_whitespace(self):
        tag = Tag.objects.create(name=" test ")
        self.assertEqual(tag.name, "test")

    def test_empty_tag_not_created(self):
        with self.assertRaises(ValidationError):
            Tag.objects.create(name="")
        with self.assertRaises(ValidationError):
            Tag.objects.create(name=" ")
        with self.assertRaises(ValidationError):
            Tag.objects.create(name="  ")

    def test_tag_remove_punctuation(self):
        # Create a tag with punctuation
        tag = Tag.objects.create(name="hello,world!")
        self.assertEqual(tag.name, "helloworld")

    def test_tag_empty_after_punctuation_removed(self):
        # Try to create a tag that's only punctuation, should raise ValidationError
        with self.assertRaises(ValidationError):
            Tag.objects.create(name="!@#$%^&*()")

    def test_tag_remove_punctuation_start(self):
        # Punctuation at the start
        tag = Tag.objects.create(name="!start")
        self.assertEqual(tag.name, "start")

    def test_tag_remove_punctuation_middle(self):
        # Punctuation in the middle
        tag = Tag.objects.create(name="mid!dle")
        self.assertEqual(tag.name, "middle")

    def test_tag_remove_punctuation_end(self):
        # Punctuation at the end
        tag = Tag.objects.create(name="end!")
        self.assertEqual(tag.name, "end")

    def test_tag_remove_various_punctuation(self):
        # String with various types of punctuation
        tag = Tag.objects.create(name="!various.punctuation,here;")
        self.assertEqual(tag.name, "variouspunctuationhere")

    def test_tag_punctuation_only(self):
        # String with punctuation only
        with self.assertRaises(ValidationError):
            Tag.objects.create(name="!?.")

    def test_tag_punctuation_with_spaces(self):
        # String with punctuation and spaces
        tag = Tag.objects.create(name=" punc!tua tion ")
        self.assertEqual(tag.name, "punctuation")

    def test_tag_unique_after_punctuation_removal(self):
        # Ensuring uniqueness after punctuation removal
        Tag.objects.create(name="unique-tag")
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="unique!tag")
