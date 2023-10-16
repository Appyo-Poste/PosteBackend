import pprint

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.forms import URLField
from rest_framework import serializers

# import models
from .models import Folder, Post, User


# Create serializers here
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserCreateSerializer(serializers.ModelSerializer):
    # Allow the serializer to accept name, but not require it
    name = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        """
        Currently, the app passes 'name' as a string, but in the future we want to move
        to passing 'first_name' and 'last_name' separately. This is a temporary solution
        to allow both to work.
        """

        model = User
        fields = ["email", "password", "first_name", "last_name", "name"]
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def to_internal_value(self, data):
        """
        Ensures that email is always lowercase before validation or creation methods

        Also allows the serializer to accept 'name' as a string, but not require it
        If a user provides "first_name" and "last_name" it will use these values, even
        if they also provide "name".

        If a user provides "name" but not "first_name" or "last_name", it will split the
        name on the first space and use the first part as "first_name" and the rest as
        "last_name"

        This allows us to continue to accept "name" while providing room to move to
        "first_name" and "last_name" in the future, as Django expects.
        """
        ret = super().to_internal_value(data)
        ret["email"] = ret["email"].lower()
        if "name" in ret and not all(k in ret for k in ["first_name", "last_name"]):
            first_name, last_name = self.split_full_name(ret["name"])
            ret["first_name"] = first_name
            ret["last_name"] = last_name

        # Remove 'name' from the data, so it doesn't get passed to the User model
        ret.pop("name", None)
        return ret

    def validate(self, data):
        # Ensure that first_name or name is passed
        if not data.get("first_name") and not data.get("name"):
            raise serializers.ValidationError("You must provide a name")
        return data

    def validate_email(self, value):  # noqa
        # Check if email is taken
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        # Check if email is blank
        if value.strip() == "":
            raise serializers.ValidationError("Email cannot be blank")
        return value

    def validate_password(self, value):  # noqa
        # Check if password is blank
        if value.strip() == "":
            raise serializers.ValidationError("Password cannot be blank")
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters")
        return value

    def split_full_name(self, name):  # noqa
        name_parts = name.split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        return first_name, last_name


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"
        extra_kwargs = {
            "title": {"required": True},
            "url": {"required": True},
        }

    def create(self, validated_data):
        post = Post(
            title = validated_data["title"],
            description = validated_data["description"],
            url = validated_data["url"],
            creator = validated_data["creator"],
            folder = validated_data["folder"]
        )
        return post

    def validate_url(self, value):
        url_form_field = URLField()
        try:
            url = url_form_field.clean(value)
        except ValidationError:
            raise serializers.ValidationError("invalid url")
        return url


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ["title", "creator", "shared_users", "pk"]


class FolderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ["title", "creator", "pk"]
        extra_kwargs = {
            "title": {"required": True},
            "creator": {"required": True},
        }

    def create(self, validated_data):
        folder = Folder(
            title = validated_data["title"],
            creator = validated_data["creator"],
        )
        return folder