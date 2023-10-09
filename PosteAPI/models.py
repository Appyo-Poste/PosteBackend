from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        self.username = self.email
        return super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.email


class Folder(models.Model):
    folderId = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_users = models.ManyToManyField(
        User, related_name="shared_folders", blank=True
    )
    stored_posts = models.ManyToManyField(
        'Post', related_name="folder", blank=True
    )


    def __str__(self):
        return self.id


class Post(models.Model):
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1000, blank=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    folder_location = models.ForeignKey(Folder, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
