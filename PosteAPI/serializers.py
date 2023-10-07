from django.core.exceptions import ValidationError
from django.core.validators import validate_email
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
    name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        name = validated_data.get("name")
        first_name, last_name = self.split_full_name(name)
        user = User(
            email=validated_data["email"],
            username=validated_data["email"],
            first_name=first_name,
            last_name=last_name,
        )
        print(validated_data["password"])
        user.set_password(validated_data["password"])
        user.save()
        return user

    def to_internal_value(self, data):
        """
        Ensures that email is always lowercase before validation or creation methods
        """
        ret = super().to_internal_value(data)
        ret["email"] = ret["email"].lower()
        return ret

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


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = "__all__"
