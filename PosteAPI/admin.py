# Register your models here.
from django.contrib import admin

from .models import Folder, Post, User, FolderPermission


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name')
    # order by email alphabetically
    ordering = ['id']


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'url', 'folder', 'creator')
    # order by folder alphabetically
    ordering = ['folder__title']


class FolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'creator')
    # order by creator and title alphabetically
    ordering = ['creator', 'title']


class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'folder', 'permission')
    # order by folder alphabetically
    ordering = ('folder__title',)


admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(FolderPermission, FolderPermissionAdmin)
