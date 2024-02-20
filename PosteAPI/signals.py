from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import Folder


@receiver(post_save, sender=get_user_model())
def create_root_folder(sender, instance, created, **kwargs):
    if created:
        Folder.objects.create(title="root", creator=instance, is_root=True)
