# Register your models here.
from django.contrib import admin
from django.core.checks import messages
from django.core.exceptions import ValidationError

from .models import Folder, FolderPermission, Post, Tag, User


class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "created_at")
    # order by email alphabetically
    ordering = ["id"]
    readonly_fields = ("created_at",)


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

    list_display = ("name", "post_count")  # what to show in the list
    ordering = ["name"]  # order by name alphabetically
    inlines = [
        PostInline
    ]  # show PostInline in the Tag admin page (to show posts using this tag)

    def post_count(self, obj):
        """
        Used in admin page to count number of posts using this tag
        """
        return obj.posts.count()

    post_count.short_description = (
        "Posts using this tag"  # show this as the column name
    )
    post_count.admin_order_field = (
        "post_count"  # If we sort by this column, here's how we sort
    )


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

    list_display = (
        "id",
        "title",
        "url",
        "folder",
        "creator",
        "tag_count",
        "created_at",
    )  # what to show in the list
    ordering = ["folder__title"]  # order by folder alphabetically
    inlines = [
        TagInline
    ]  # show TagInline in the Post admin page (to show tags used by this post)
    exclude = (
        "tags",
    )  # don't show tags field in the Post admin page, using TagInline instead
    readonly_fields = ("created_at",)

    def tag_count(self, obj):
        """
        Used in admin page to count number of tags used by this post
        """
        return obj.tags.count()

    tag_count.short_description = "Tag count"  # show this as the column name
    tag_count.admin_order_field = (
        "tag_count"  # If we sort by this column, here's how we sort
    )


class FolderAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "creator", "created_at")
    # order by creator and title alphabetically
    ordering = ["creator", "title"]
    readonly_fields = ("created_at",)

    def can_delete_obj(self, obj):
        return obj.is_root is False or obj.creator_id is None

    def delete_model(self, request, obj):
        if self.can_delete_obj(obj):
            super().delete_model(request, obj)
        else:
            raise ValidationError(
                "Cannot delete root folder unless the user is being deleted."
            )

    def delete_queryset(self, request, queryset):
        deletable_objects = [obj for obj in queryset if self.can_delete_obj(obj)]
        non_deletable_objects = queryset.exclude(
            pk__in=[obj.pk for obj in deletable_objects]
        )

        for obj in non_deletable_objects:
            self.message_user(
                request, f"Cannot delete root folder: {obj.title}", level=messages.ERROR
            )

        deletable_queryset = self.model.objects.filter(
            pk__in=[obj.pk for obj in deletable_objects]
        )
        deletable_queryset.delete()
        self.message_user(
            request,
            f"Successfully deleted {len(deletable_objects)} folder(s).",
            level=messages.INFO,
        )

    def delete_selected(self, request, queryset):
        self.delete_queryset(request=request, queryset=queryset)

    # Assign the new action to the list of actions available
    actions = [delete_selected]


class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "folder", "permission")
    # order by folder alphabetically
    ordering = ("folder__title",)


admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Folder, FolderAdmin)
admin.site.register(FolderPermission, FolderPermissionAdmin)
