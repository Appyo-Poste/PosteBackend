from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    def create_folder(self, title):
        return Folder.objects.create(title=title, creator=self)

    def create_post(self, title, url, folder):
        return Post.objects.create(title=title, url=url, creator=self, folder=folder)

    # @TODO update given FolderPermission
    def can_see_folder(self, folder):
        return folder.creator == self or self in folder.shared_users.all()

    # @TODO update given FolderPermission
    def can_see_post(self, post):
        return self.can_see_folder(post.folder)

    def create_post_and_folder(self, title, description, url, folder_title):
        folder = Folder.objects.create(title=folder_title, creator=self)
        post = Post.objects.create(
            title=title, description=description, url=url, creator=self, folder=folder
        )
        return post, folder

    # @TODO update given FolderPermission
    def share_folder_with_user(self, folder, user):
        if folder.creator != self:
            raise Exception("You are not the creator of this folder")
        folder.shared_users.add(user)

    # @TODO update given FolderPermission
    def unshare_folder_with_user(self, folder, user):
        if folder.creator != self:
            raise Exception("You are not the creator of this folder")
        folder.shared_users.remove(user)

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


class Post(models.Model):
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1000)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class FolderPermission(models.Model):
    # why gettext_lazy?
    # https://stackoverflow.com/questions/54802616/how-can-one-use-enums-as-a-choice-field-in-a-django-model
    class FolderPermissionEnum(models.TextChoices):
        # a viewer can only view posts within a folder
        VIEWER = 'viewer', gettext_lazy('Viewer')
        # an editor can add posts to a folder, edit existing posts, and delete posts
        EDITOR = 'editor', gettext_lazy('Editor')
        # a full access user is an editor who can share the folder with other users
        FULL_ACCESS = 'full_access', gettext_lazy('Full Access')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    permission = models.CharField(max_length=12, choices=FolderPermissionEnum.choices)

    def __str__(self):
        return f"{self.user.username} has {self.permission} permission within {self.folder.title}"
