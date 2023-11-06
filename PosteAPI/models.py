from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    def create_folder(self, title):
        folder = Folder.objects.create(title=title, creator=self)
        # Previously, we forced permission creation. By including a check in the save method of the Folder model,
        # this is no longer necessary, as the permission will be created automatically.
        if not FolderPermission.objects.filter(user=self, folder=folder).exists():
            FolderPermission.objects.create(
                user=self,
                folder=folder,
                permission=FolderPermissionEnum.FULL_ACCESS
            )
        return folder

    def create_post(self, title, url, folder):
        return Post.objects.create(title=title, url=url, creator=self, folder=folder)

    def can_view_folder(self, folder):
        return FolderPermission.objects.filter(
            user=self, folder=folder, permission__in=[
                FolderPermissionEnum.FULL_ACCESS, FolderPermissionEnum.EDITOR, FolderPermissionEnum.VIEWER]).exists()

    def can_view_post(self, post):
        return self.can_view_folder(post.folder)

    def can_edit_folder(self, folder):
        return FolderPermission.objects.filter(
            user=self, folder=folder, permission__in=[
                FolderPermissionEnum.FULL_ACCESS, FolderPermissionEnum.EDITOR]).exists()

    def can_edit_post(self, post):
        return self.can_edit_folder(post.folder)

    def can_share_folder(self, folder):
        return FolderPermission.objects.filter(
            user=self, folder=folder, permission__in=[
                FolderPermissionEnum.FULL_ACCESS]).exists()

    def can_share_post(self, post):
        return self.can_share_folder(post.folder)

    def create_post_and_folder(self, title, description, url, folder_title):
        folder = Folder.objects.create(title=folder_title, creator=self)
        post = Post.objects.create(
            title=title, description=description, url=url, creator=self, folder=folder
        )
        return post, folder

    def share_folder_with_user(self, folder, user, permission):
        if not self.can_share_folder(folder):
            raise Exception("You do not have permission to share this folder.")
        FolderPermission.objects.create(
            user=user,
            folder=folder,
            permission=permission
        )

    def unshare_folder_with_user(self, folder, user):
        if not self.can_share_folder(folder):
            raise Exception("You do not have permission to unshare this folder.")
        folder_permission = FolderPermission.objects.get(
            user=user,
            folder=folder
        )
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
    title = models.CharField(max_length=100, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        If the folder is new, create a folder permission for the creator with full access if it doesn't exist.
        Ensures that the creator always has full access to their own folders.
        """
        is_new = not self.pk    # Only applies to new folders (save can be called on existing folders)
        super().save(*args, **kwargs)
        if is_new and not FolderPermission.objects.filter(user=self.creator, folder=self).exists():
            FolderPermission.objects.create(
                user=self.creator,
                folder=self,
                permission=FolderPermissionEnum.FULL_ACCESS,
            )


class Post(models.Model):
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1000, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts')


    def edit(self, newTitle, newDescription, newURL):
        self.title = newTitle
        self.description = newDescription
        self.url = newURL
        self.save()

    def __str__(self):
        return self.title

class Tag(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True)
    # This will automatically have a reverse relationship to Posts

    def __str__(self):
        return self.name


# why gettext_lazy?
# https://stackoverflow.com/questions/54802616/how-can-one-use-enums-as-a-choice-field-in-a-django-model
class FolderPermissionEnum(models.TextChoices):
    # a viewer can only view posts within a folder
    VIEWER = 'viewer', gettext_lazy('Viewer')
    # an editor can add posts to a folder, edit existing posts, and delete posts
    EDITOR = 'editor', gettext_lazy('Editor')
    # a full access user is an editor who can share the folder with other users
    FULL_ACCESS = 'full_access', gettext_lazy('Full Access')


class FolderPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    permission = models.CharField(max_length=12, choices=FolderPermissionEnum.choices)

    def __str__(self):
        return f"{self.user.username} has {self.permission} permission within {self.folder.title}"
