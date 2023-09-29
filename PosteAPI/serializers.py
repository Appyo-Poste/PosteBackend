from rest_framework import serializers

# import models
from .models import Folder, Post, User


# Create serializers here
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # pass all fields but password
        fields = ["id", "name", "email"]


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(write_only=True, max_length=100)


class PostSerializer(serializers.ModelSerializer):
    # TODO
    class Meta:
        model = Post
        fields = "__all__"


class FolderSerializer(serializers.ModelSerializer):
    # TODO
    class Meta:
        model = Folder
        fields = "__all__"
