from django.contrib.contenttypes.models import ContentType
from django.test import TestCase


class DefaultModelTests(TestCase):
    def test_user_exists(self):
        is_exists = ContentType.objects.filter(model="user").exists()
        self.assertTrue(is_exists)

    def test_post_exists(self):
        is_exists = ContentType.objects.filter(model="post").exists()
        self.assertTrue(is_exists)

    def test_folder_exists(self):
        is_exists = ContentType.objects.filter(model="folder").exists()
        self.assertTrue(is_exists)
