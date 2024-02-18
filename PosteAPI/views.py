import json

from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Folder, FolderPermission, Post, Tag, User

# import local data
from .serializers import (
    FolderCreateSerializer,
    FolderSerializer,
    PostCreateSerializer,
    PostSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserSerializer,
)


# Create views / viewsets here.
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="This endpoint allows a user to log in by using their email and password.",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login Successful",
                schema=UserSerializer(many=False),
                examples={
                    "application/json": {
                        "result": {
                            "success": True,
                            "token": "abcdefg12345678",
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "result": {
                            "success": False,
                            "errors": {
                                "email": ["This field is required."],
                                "password": ["This field is required."],
                            },
                        }
                    }
                },
            ),
            401: openapi.Response(
                description="Invalid email or password",
                examples={"application/json": {"result": {"success": False}}},
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            password = serializer.validated_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {"result": {"success": True, "token": token.key}},
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {"result": {"success": False}}, status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            return Response(
                {"result": {"success": False, "errors": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DataView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    token_param = openapi.Parameter(
        "Authorization",
        openapi.IN_HEADER,
        description="The string 'Token' and the user's token. Example:'Token abcd1234",
        type=openapi.TYPE_STRING,
        required=True,
    )

    @swagger_auto_schema(manual_parameters=[token_param])
    def get(self, request, folder_id=None):
        if folder_id:
            folder = Folder.objects.filter(id=folder_id).first()
            print("Got specific folder: " + str(folder))
        else:
            folder = Folder.objects.filter(creator=request.user, is_root=True).first()
            print("Got root")

        if not folder:
            return Response({"error": "Folder not found"}, status=404)

        own_folders = Folder.objects.filter(creator=request.user, parent=folder)
        own_posts = Post.objects.filter(folder=folder)

        folder_serializer = FolderSerializer(own_folders, many=True)
        post_serializer = PostSerializer(own_posts, many=True)
        # All GET will get this information
        response_dic = {
            "folders": folder_serializer.data,
            "posts": post_serializer.data,
        }

        # If in root, add shared folder
        if folder.is_root:
            folder_perms = FolderPermission.objects.filter(
                user=request.user, permission__isnull=False
            ).prefetch_related("folder")
            shared_folders = [perm.folder for perm in folder_perms]
            shared_folder_serializer = FolderSerializer(shared_folders, many=True)
            response_dic["shared_folders"] = shared_folder_serializer.data

        return Response(response_dic, status=200)


class UsersView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Returns a list of all users",
        responses={
            200: UserSerializer(many=True),
            400: "Bad Request",
        },
    )
    def get(self, request):
        """
        Returns a list of all users
        """
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Creates a new user.",
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="The created user object.", schema=UserSerializer
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "email": [
                            "Email is not valid",
                            "Email already in use",
                            "Email cannot be blank",
                        ],
                        "password": ["Password cannot be blank"],
                        "name": ["Name cannot be blank"],
                    }
                },
            ),
        },
    )
    def post(self, request):
        """
        Creates a new user
        """
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = Response(status=status.HTTP_201_CREATED)
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if user is None:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserSerializer(user)
        return Response(serializer.data)


class ChangePassword(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Edits a user's password
        """
        user_id = Token.objects.get(key=request.auth.key).user_id
        user = User.objects.get(id=user_id)
        data = json.loads(request.body.decode("utf-8"))
        newPassword = data.get("newPassword")
        oldPassword = data.get("oldPassword")
        if user.check_password(oldPassword):
            if user.check_password(newPassword):
                message = "New password cannot be same as old password"
                return Response(
                    {"result": {"success": False}, "error": message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                user.set_password(newPassword)
                user.save()
                if hasattr(user, "auth_token"):
                    user.auth_token.delete()
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {"result": {"success": True, "token": token.key}},
                    status=status.HTTP_200_OK,
                )

        else:
            message = "Old password does not match"
            return Response(
                {"result": {"success": False}, "error": message},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class FolderAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Returns a list of all folders",
        responses={
            200: FolderSerializer(many=True),
            400: "Bad Request",
        },
    )
    def get(self, request):
        folders = Folder.objects.all()
        serializer = FolderSerializer(folders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Creates a new folder.",
        request_body=FolderCreateSerializer,
        responses={
            201: openapi.Response(
                description="The created folder object.", schema=FolderSerializer
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "title": ["title cannot be blank"],
                        "creator": ["creator is not a valid user"],
                    }
                },
            ),
        },
    )
    def post(self, request):
        serializer = FolderCreateSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            Folder.objects.create(creator=request.user, **validated_data)
            return Response(status=status.HTTP_201_CREATED)
        else:
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            # error message contained in response.data
            return response


class FolderForUser(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get_owned(self, user):
        return Folder.objects.filter(creator=user)

    def get_shared(self, user):
        if FolderPermission.objects.filter(user=user).exists():
            shared = None
            for permission in FolderPermission.objects.filter(user=user):
                if shared is None:
                    shared = Folder.objects.filter(pk=permission.folder.pk)
                else:
                    shared = shared | Folder.objects.filter(pk=permission.folder.pk)
            return shared
        else:
            return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if user is None:
            return Response(
                {"error": "User does not exist", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        owned_folders = self.get_owned(user)
        shared_folders = self.get_shared(user)
        folders = None

        if owned_folders is None and shared_folders is None:
            return Response(
                {"error": "User has no folders", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )
        elif owned_folders is None:
            folders = shared_folders
        elif shared_folders is None:
            folders = owned_folders
        else:
            folders = shared_folders | owned_folders

        serializer = FolderSerializer(folders, many=True)
        return Response(
            {"success": True, "folders": serializer.data}, status=status.HTTP_200_OK
        )


class PostAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Returns a list of all posts",
        responses={
            200: PostSerializer(many=True),
            400: "Bad Request",
        },
    )
    def get(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Creates a new Post.",
        request_body=FolderCreateSerializer,
        responses={
            201: openapi.Response(
                description="The created Post object.", schema=PostSerializer
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "title": ["title cannot be blank"],
                        "creator": ["creator is not a valid user"],
                    }
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        try:
            serializer = PostCreateSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.validated_data["creator"] = request.user
                serializer.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                print("Error: ", serializer.errors)
                response = Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
                return response
        except Exception as e:
            print("Error: ", e)


class IndividualPostView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        """
        Delete a post
        :param request: Request object
        :param id: Post id as path parameter
        """
        try:
            post = Post.objects.get(pk=id)
        except Post.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "errors": {"post": ["Specified post does not exist"]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {
                    "success": False,
                    "errors": {"post": ["Server error occurred while deleting post"]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.delete()
        return Response(
            {
                "success": True,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request: Request, id: int):
        """
        Edits a post in the server
        :param request: Request object with post id and auth in header
                        Request Body contains new title, description and url
        """
        try:
            post = Post.objects.get(pk=id)
        except Post.DoesNotExist as e:
            message = "Post does not exist"
            print(f"{message}. Error: {e}")
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Post.MultipleObjectsReturned as e:
            message = "Multiple Posts found with that ID"
            print(f"{message}. Error: {e}")
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = json.loads(request.body.decode("utf-8"))
        try:
            tags_merged = data.get("tags")
            tag_names = [tag.strip() for tag in tags_merged.split(", ") if tag.strip()]
        except Exception as e:
            print(f"Error: {e}")
            return Response(
                {"success": False, "errors": {"post": ["Error parsing tags"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tag_list = []
        if tag_names:
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                print(f"Tag: {tag}, Created: {created}")
                tag_list.append(tag)
        post.edit(data.get("title"), data.get("description"), data.get("url"), tag_list)
        return Response({"success": True}, status=status.HTTP_200_OK)


class AddPostToFolder(APIView):
    def get_object(self, pk):
        try:
            return Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return None

    def get_post(self, pk2):
        try:
            return Post.objects.get(pk=pk2)
        except Post.DoesNotExist:
            return None

    def get(self, request, pk, pk2):
        folder = self.get_object(pk)
        if folder is None:
            return Response(
                {"error": "folder does not exist", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        post = self.get_post(pk2)
        if post is None:
            return Response(
                {"error": "post does not exist", "success": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        post.folder = folder
        post.save()

        return Response({"success": True}, status=status.HTTP_200_OK)


class deleteFolder(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return None

    def delete(self, request, pk):
        # TODO: Check permissions
        try:
            folder = self.get_object(pk)
            if folder is not None:
                folder.delete()
                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"success": False, "Error": "folder does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception:
            return Response(
                {"success": False, "Error": "Bad request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get(self, request, pk):
        folder = self.get_object(pk)
        if folder is not None:
            folder.delete()
            return Response({"success": True}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"success": False, "Error": "folder does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FolderDetail(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return None

    def get(self, request, pk):
        folder = self.get_object(pk)
        if folder is None:
            return Response(
                {"error": "Folder not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = FolderSerializer(folder)
        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            folder = self.get_object(pk)
            folder.edit(request.data["title"])
            return Response({"success": True}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            message = "Folder does not exist"
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            message = "Server error occurred while editing folder"
            print(f"{message}: {e}")
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
