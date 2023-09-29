from django.db import models

# Create your models here.


class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)


class Post(models.Model):
    pass


class Folder(models.Model):
    pass
