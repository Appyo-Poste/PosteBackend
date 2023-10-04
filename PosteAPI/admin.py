# Register your models here.
from django.contrib import admin

from .models import Folder, Post, User

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Folder)
