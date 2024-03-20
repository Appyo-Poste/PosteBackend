import os

import django

from PosteAPI.models import Folder, User

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PosteBackend.settings")
print("DJANGO_SETTINGS_MODULE:", os.environ.get("DJANGO_SETTINGS_MODULE"))
django.setup()


superuser_email = "admin@email.com"
superuser_username = superuser_email  # Using the email as username
superuser_first_name = "user"
superuser_last_name = "user"
superuser_password = "Admin1234"

if not User.objects.filter(username=superuser_username).exists():
    admin = User.objects.create_superuser(
        email=superuser_email,
        username=superuser_username,
        first_name=superuser_first_name,
        last_name=superuser_last_name,
        password=superuser_password,
    )
    print("Superuser created successfully.")
else:
    admin = None
    print("Superuser already exists.")

# Create a regular user
user_email = "user@email.com"
user_username = user_email  # Using the email as username
user_password = "user1234"

if not User.objects.filter(username=user_username).exists():
    user = User.objects.create_user(
        email=user_email, username=user_username, password=user_password
    )
    print("Regular user created successfully.")
else:
    user = None
    print("Regular user already exists.")

if admin:
    root_folder = Folder.objects.get(creator=admin, is_root=True)
    folder1 = Folder.objects.create(
        title="Admin Folder 1 (in root)",
        creator=admin,
        is_root=False,
        parent=root_folder,
    )
    folder2 = Folder.objects.create(
        title="Admin Folder 2 (in root)",
        creator=admin,
        is_root=False,
        parent=root_folder,
    )
    folder3 = Folder.objects.create(
        title="Admin Folder 3 (in Folder1)",
        creator=admin,
        is_root=False,
        parent=folder1,
    )
    folder4 = Folder.objects.create(
        title="Admin Folder 4 (in Folder3)",
        creator=admin,
        is_root=False,
        parent=folder3,
    )

if user:
    root_folder = Folder.objects.get(creator=user, is_root=True)
    folder1 = Folder.objects.create(
        title="User Folder 1 (in root)", creator=user, is_root=False, parent=root_folder
    )
    folder2 = Folder.objects.create(
        title="User Folder 2 (in root)", creator=user, is_root=False, parent=root_folder
    )
    folder3 = Folder.objects.create(
        title="User Folder 3 (in User Folder 1)",
        creator=user,
        is_root=False,
        parent=folder1,
    )
    folder4 = Folder.objects.create(
        title="User Folder 4 (in User Folder 3)",
        creator=user,
        is_root=False,
        parent=folder3,
    )
