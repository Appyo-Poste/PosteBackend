from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    def create_folder(self, title):
        return Folder.objects.create(title=title, creator=self)

    def create_post(self, title, url, folder):
        return Post.objects.create(title=title, url=url, creator=self, folder=folder)

    def can_see_folder(self, folder):
        return folder.creator == self or self in folder.shared_users.all()

    def can_see_post(self, post):
        return self.can_see_folder(post.folder)

    def create_post_and_folder(self, title, description, url, folder_title):
        folder = Folder.objects.create(title=folder_title, creator=self)
        post = Post.objects.create(
            title=title, description=description, url=url, creator=self, folder=folder
        )
        return post, folder

    def share_folder_with_user(self, folder, user):
        if folder.creator != self:
            raise Exception("You are not the creator of this folder")
        folder.shared_users.add(user)

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
    shared_users = models.ManyToManyField(
        User, related_name="shared_folders", blank=True
    )

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
