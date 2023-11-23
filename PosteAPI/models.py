import string

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    def save(self, *args, **kwargs):
        # Make username the same as email
        self.username = self.email
        super(User, self).save(*args, **kwargs)

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
        Unshare a folder with a specific target user.
        If the target user has shared the folder with other users, redirect those
        Shares such that the current user is the source of the share.
        This ensures that these Shares are still controlled.
        """
        # Retrieve the share instance between self and target
        share = Share.objects.get(source=self, target=target, folder=folder)

        # Reassign target users share source to self
        target_shares = Share.objects.filter(source=target, folder=folder)
        for target_share in target_shares:
            try:
                # Check if a similar share already exists
                existing_share = Share.objects.filter(
                    source=self, target=target_share.target, folder=folder
                )
                if existing_share.exists():
                    #  Don't need to reassign the share if it already exists
                    target_share.delete()
                else:
                    # Otherwise, reassign the share
                    target_share.source = self
                    target_share.save()
            except IntegrityError as e:
                print("Error reassigning share: ", e)
                pass

        # Finally, delete the original share with the target user
        share.delete()

    def share_folder_with_user(self, folder, user, permission):
        if not self.can_share_folder(folder):
            raise Exception("You do not have permission to share this folder.")
        Share.objects.get_or_create(
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
