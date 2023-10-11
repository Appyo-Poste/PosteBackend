# Register your models here.
from django.contrib import admin

from .models import Folder, Post, User, FolderPermission

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Folder)
admin.site.register(FolderPermission)
