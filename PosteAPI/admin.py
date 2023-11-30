# Register your models here.
from django.contrib import admin

from .models import Folder, Post, User, FolderPermission, Tag


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name')
    # order by email alphabetically
    ordering = ['id']


class PostInline(admin.TabularInline):
    """
    Used to show Posts in the Tag admin page
    """
    model = Post.tags.through  # the query goes through the Post model
    extra = 1  # how many rows to show by default


class TagAdmin(admin.ModelAdmin):
    """
    Defines Tag admin page
    """
    list_display = ('name', 'post_count')  # what to show in the list
    ordering = ['name']  # order by name alphabetically
    inlines = [PostInline]  # show PostInline in the Tag admin page (to show posts using this tag)

    def post_count(self, obj):
        """
        Used in admin page to count number of posts using this tag
        """
        return obj.posts.count()

    post_count.short_description = 'Posts using this tag'  # show this as the column name
    post_count.admin_order_field = 'post_count'  # If we sort by this column, here's how we sort


class TagInline(admin.TabularInline):
    """
    Used to show tags in the Post admin page
    """
    model = Post.tags.through
    extra = 1


class PostAdmin(admin.ModelAdmin):
    """
    Defines Post admin page
    """
    list_display = ('id', 'title', 'url', 'folder', 'creator', 'tag_count')  # what to show in the list
    ordering = ['folder__title']  # order by folder alphabetically
    inlines = [TagInline]  # show TagInline in the Post admin page (to show tags used by this post)
    exclude = ('tags',)  # don't show tags field in the Post admin page, using TagInline instead

    def tag_count(self, obj):
        """
        Used in admin page to count number of tags used by this post
        """
        return obj.tags.count()

    tag_count.short_description = 'Tag count'  # show this as the column name
    tag_count.admin_order_field = 'tag_count'  # If we sort by this column, here's how we sort


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
admin.site.register(Tag, TagAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(FolderPermission, FolderPermissionAdmin)
