from django.apps import AppConfig


class PosteapiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "PosteAPI"

    def ready(self):
        import PosteAPI.signals
