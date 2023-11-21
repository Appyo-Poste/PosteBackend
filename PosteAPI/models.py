import string

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    def create_folder(self, title):
        folder = Folder.objects.create(title=title, creator=self)
        return folder

    def create_post(self, title, url, folder):
        return Post.objects.create(title=title, url=url, creator=self, folder=folder)

    def can_view_folder(self, folder):
        return (
            self == folder.creator
            or Share.objects.filter(
                target=self, folder=folder, permission__isnull=False
            ).exists()
        )

    def can_view_post(self, post):
        return self.can_view_folder(post.folder)

    def can_edit_folder(self, folder):
        return (
            self == folder.creator
            or Share.objects.filter(
                target=self,
                folder=folder,
                permission__in=[
                    FolderPermissionEnum.EDITOR,
                    FolderPermissionEnum.FULL_ACCESS,
                ],
            ).exists()
        )

    def can_edit_post(self, post):
        return self.can_edit_folder(post.folder)

    def can_share_folder(self, folder):
        return (
            self == folder.creator
            or Share.objects.filter(
                target=self,
                folder=folder,
                permission__in=[FolderPermissionEnum.FULL_ACCESS],
            ).exists()
        )

    def can_share_post(self, post):
        return self.can_share_folder(post.folder)

    def create_post_and_folder(self, title, description, url, folder_title):
        folder = Folder.objects.create(title=folder_title, creator=self)
        post = Post.objects.create(
            title=title, description=description, url=url, creator=self, folder=folder
        )
        return post, folder

    def unshare_folder_recursively(self, folder, source_user):
        """
        Recursively unshare the folder with users who were shared the folder by source_user.
        """
        # Find all users who were shared this folder by source_user
        forward_shares = Share.objects.filter(source=source_user, folder=folder)

        for share in forward_shares:
            # Recursively unshare the folder for each user in forward_shares
            target_user = share.target
            self.unshare_folder_recursively(folder, target_user)

            # After handling all forward shares, delete the current share
            share.delete()

    def unshare_folder_with_target(self, folder, target):
        """
        Unshare a folder with a specific target user and ensure they unshare it with anyone they shared it with.
        """
        share = Share.objects.filter(source=self, target=target, folder=folder)
        if not share.exists():
            raise Share.DoesNotExist
        elif share.count() > 1:
            raise Share.MultipleObjectsReturned
        # First, handle the cascade of unshares
        self.unshare_folder_recursively(folder, target)

        # Then, delete the original share between the user and the target, if it exists
        share.delete()

    def share_folder_with_user(self, folder, user, permission):
        if not self.can_share_folder(folder):
            raise Exception("You do not have permission to share this folder.")
        Share.objects.create(
            source=self, target=user, folder=folder, permission=permission
        )

    def __str__(self):
        return self.email


class Folder(models.Model):
    title = models.CharField(max_length=100, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField("Tag", blank=True, related_name="folder")

    def __str__(self):
        return self.title

    def edit(self, newTitle):
        self.title = newTitle
        self.save()


class Post(models.Model):
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1000, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    tags = models.ManyToManyField("Tag", blank=True, related_name="posts")

    def edit(self, newTitle, newDescription, newURL):
        self.title = newTitle
        self.description = newDescription
        self.url = newURL
        self.save()

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True)
    # This will automatically have a reverse relationship to Posts and Folders

    def save(self, *args, **kwargs):
        """
        Saves the Tag instance after processing the name attribute.

        The name is stripped of punctuation, converted to lowercase, and any form of whitespace
        is removed. If the name is empty after processing, a ValidationError is raised to prevent
        saving an invalid tag.

        Raises:
            ValidationError: If the processed name is empty.
        """
        self.name = self.name.translate(
            str.maketrans("", "", string.punctuation)
        )  # remove punctuation
        self.name = self.name.lower()  # lowercase
        self.name = "".join(
            self.name.split()
        )  # remove all whitespace, including internal
        if not self.name:
            raise ValidationError("Tag name cannot be empty.")
        return super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


# why gettext_lazy?
# https://stackoverflow.com/questions/54802616/how-can-one-use-enums-as-a-choice-field-in-a-django-model
class FolderPermissionEnum(models.TextChoices):
    # a viewer can only view posts within a folder
    VIEWER = "viewer", gettext_lazy("Viewer")
    # an editor can add posts to a folder, edit existing posts, and delete posts
    EDITOR = "editor", gettext_lazy("Editor")
    # a full access user is an editor who can share the folder with other users
    FULL_ACCESS = "full_access", gettext_lazy("Full Access")


class Share(models.Model):
    source = models.ForeignKey(User, on_delete=models.CASCADE, related_name="source")
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name="target")
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    permission = models.CharField(
        max_length=12,
        choices=FolderPermissionEnum.choices,
        blank=False,
        null=False,
        default=FolderPermissionEnum.VIEWER,
    )

    class Meta:
        unique_together = ("source", "target", "folder")
