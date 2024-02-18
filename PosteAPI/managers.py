from django.db import models


class FolderManager(models.Manager):
    def create(self, *args, **kwargs):
        if (
            "parent" not in kwargs or kwargs["parent"] is None
        ):  # if parent isn't specified
            root_folder = (
                super()
                .get_queryset()
                .filter(is_root=True, creator=kwargs["creator"])
                .first()
            )  # get root folder for the creator
            kwargs["parent"] = root_folder
        return super().create(*args, **kwargs)
