# Register your models here.
from django.contrib import admin

from .models import Folder, Post

admin.site.register(Post)
admin.site.register(Folder)
