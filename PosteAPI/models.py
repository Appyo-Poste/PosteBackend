import string

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy

from PosteAPI.managers import FolderManager


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def unshare_folder_with_target(self, folder, target):
        folder_permissions = FolderPermission.objects.filter(user=target, folder=folder)
        if not folder_permissions:
            raise FolderPermission.DoesNotExist("Folder not shared with target user.")
        for folder_permission in folder_permissions:
            folder_permission.delete()

    def create_folder(self, title) -> "Folder":
        folder = Folder.objects.create(title=title, creator=self)
        # Previously, we forced permission creation. By including a check in the save method of the Folder model,
        # this is no longer necessary, as the permission will be created automatically.
        if not FolderPermission.objects.filter(user=self, folder=folder).exists():
            FolderPermission.objects.create(
                user=self, folder=folder, permission=FolderPermissionEnum.FULL_ACCESS
            )
        return folder

    def create_post(self, title, url, folder):
        return Post.objects.create(title=title, url=url, creator=self, folder=folder)

    def can_view_folder(self, folder):
        return FolderPermission.objects.filter(
            user=self,
            folder=folder,
            permission__in=[
                FolderPermissionEnum.FULL_ACCESS,
                FolderPermissionEnum.EDITOR,
                FolderPermissionEnum.VIEWER,
            ],
        ).exists()

    def can_view_post(self, post):
        return self.can_view_folder(post.folder)

    def can_edit_folder(self, folder):
        return (
            self == folder.creator
            or FolderPermission.objects.filter(
                user=self,
                folder=folder,
                permission__in=[
                    FolderPermissionEnum.FULL_ACCESS,
                    FolderPermissionEnum.EDITOR,
                ],
            ).exists()
        )

    def can_edit_post(self, post):
        return self.can_edit_folder(post.folder)

    def has_permissions_to_share_folder(self, folder):
        return (
            self == folder.creator
            or FolderPermission.objects.filter(
                user=self,
                folder=folder,
                permission__in=[FolderPermissionEnum.FULL_ACCESS],
            ).exists()
        )

    def has_permissions_to_share_post(self, post):
        return self.has_permissions_to_share_folder(post.folder)

    def create_post_and_folder(self, title, description, url, folder_title):
        folder = Folder.objects.create(title=folder_title, creator=self)
        post = Post.objects.create(
            title=title, description=description, url=url, creator=self, folder=folder
        )
        return post, folder

    def share_folder_with_user(self, folder, user, permission):
        if self == user:
            raise ValidationError("Cannot share folder with yourself")
        if not self.has_permissions_to_share_folder(folder):
            raise ValidationError("You do not have permission to share this folder.")
        if FolderPermission.objects.filter(
            user=user, folder=folder, permission=permission
        ).exists():
            raise ValidationError("Already shared with this user")
        FolderPermission.objects.create(user=user, folder=folder, permission=permission)

    def unshare_folder_with_user(self, folder, user):
        if not self.has_permissions_to_share_folder(folder):
            raise Exception("You do not have permission to unshare this folder.")
        folder_permission = FolderPermission.objects.get(user=user, folder=folder)
        if not folder_permission:
            raise Exception("User does not have access to this folder.")
        folder_permission.delete()

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        self.username = self.email
        return super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.email


class Folder(models.Model):
    objects = FolderManager()
    title = models.CharField(max_length=100, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField("Tag", blank=True, related_name="folder")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_folders",
        default=None,
    )
    is_root = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="")

    def delete(self, *args, **kwargs):
        if (
            self.is_root
            and self.creator_id is not None
            and User.objects.filter(id=self.creator_id).exists()
        ):
            raise ValidationError(
                "Cannot delete user's root folder unless the user is being deleted."
            )
        super().delete(*args, **kwargs)

    def set_parent(self, new_parent):
        if new_parent and self in new_parent.get_ancestors():
            raise ValidationError("A folder cannot be an ancestor of itself.")
        super(Folder, self).__setattr__("parent", new_parent)

    def __setattr__(self, name, value):
        if name == "parent":
            self.set_parent(value)
        else:
            super().__setattr__(name, value)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.is_root:
            root_exists = (
                Folder.objects.filter(creator=self.creator, is_root=True)
                .exclude(pk=self.pk)
                .exists()
            )
            if root_exists:  # if a root folder exists for the same user
                raise ValidationError("A user cannot have more than one root folder.")
        elif not self.parent:  # if the folder is not root, and has no parent specified
            raise ValidationError("A non-root folder must have a parent.")
        elif self in self.parent.get_ancestors():
            raise ValidationError("A folder cannot be an ancestor of itself.")
        elif self.parent.creator != self.creator:
            raise ValidationError("A folder cannot be assigned to another user.")

    def get_ancestors(self):
        ancestors = [self]
        if self.parent:
            ancestors.extend(self.parent.get_ancestors())
        return ancestors

    def place_in_folder(self, parent_folder):
        if not parent_folder:
            raise ValidationError("Must specify a parent folder.")
        if self in parent_folder.get_ancestors():
            raise ValidationError("A folder cannot be an ancestor of itself.")
        super(Folder, self).__setattr__("parent", parent_folder)

    def __str__(self):
        return f"{self.creator} - {self.title}"


class Post(models.Model):
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1000, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="posts")
    tags = models.ManyToManyField("Tag", blank=True, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)

    def edit(self, newTitle, newDescription, newURL, newTags):
        self.title = newTitle
        self.description = newDescription
        self.url = newURL
        self.tags.set(newTags)
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


class FolderPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    permission = models.CharField(max_length=12, choices=FolderPermissionEnum.choices)

    class Meta:
        unique_together = ("user", "folder")

    def __str__(self):
        return f"{self.user.username} has {self.permission} permission within {self.folder.title}"
