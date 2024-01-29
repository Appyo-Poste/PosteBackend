import http
import json

from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Folder, FolderPermission, FolderPermissionEnum, Post, Tag, User

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


class NewDataView(generics.ListAPIView):
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
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        user = request.user
        root_folder = Folder.objects.get(creator=user, is_root=True)
        serializer = FolderSerializer(root_folder)
        return Response({"user_folders": serializer.data})


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

    def get_visible_folders(self):
        """
        Retrieve a list of folders that the user has visibility of;
        the user is either the creator, or has a FolderPermission
        """
        user = self.request.user
        folders = Folder.objects.filter(
            Q(creator=user)
            | Q(
                folderpermission__user=user,
                folderpermission__permission__in=[
                    FolderPermissionEnum.FULL_ACCESS,
                    FolderPermissionEnum.EDITOR,
                    FolderPermissionEnum.VIEWER,
                ],
            )
        ).distinct()
        return folders

    def get_shared_users(self, request_user, folders):
        """
        Returns a dictionary mapping folder ids to lists of user emails the folder is
        shared with, excluding the current.

        Only includes lists for folders the current user can share with; if the user
        cannot share a given folder (they are not the creator and don't have a
        permission) the list for a given folder id will be empty.
        """
        return {
            folder.id: (
                list(
                    FolderPermission.objects.filter(folder=folder)
                    .exclude(user=request_user)
                    .values_list("user__email", flat=True)
                    .distinct()
                )
                if request_user.can_share_folder(folder)
                else []
            )
            for folder in folders
        }

    @swagger_auto_schema(manual_parameters=[token_param])
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        get_visible_folders = self.get_visible_folders()
        context = {
            "request": request,
            "user_permissions": self.get_user_permissions(
                request.user, get_visible_folders
            ),
            "shared_users": self.get_shared_users(request.user, get_visible_folders),
        }
        serializer = self.get_serializer(
            get_visible_folders, many=True, context=context
        )
        return Response(serializer.data)

    def get_user_permissions(self, user, folders):
        """
        Generates a dictionary mapping folder.id to the folder's permission for a given user.
        If the user is the creator of the folder, they are granted FULL_ACCESS.
        Otherwise, their permission is determined by the FolderPermission model.
        :param user: User object for whom to check the permissions
        :param folders: List of Folder objects to check permissions for
        :return: Dictionary mapping folder.id to permission
        """
        folder_permissions = {}

        for folder in folders:
            if folder.creator == user:
                folder_permissions[folder.id] = FolderPermissionEnum.FULL_ACCESS
            else:
                try:
                    permission = FolderPermission.objects.get(
                        user=user, folder=folder
                    ).permission
                except FolderPermission.DoesNotExist:
                    permission = "none"
                folder_permissions[folder.id] = permission

        return folder_permissions

    @swagger_auto_schema(
        operation_description="Updates the permissions for a folder.",
        # @TODO add request_body
        # request_body= folderId, email, permission
        responses={
            200: openapi.Response(description="The folder permission was created."),
            201: openapi.Response(description="The folder permission was updated."),
            403: openapi.Response(
                description="User does not have permission to update folder permissions.",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        source = request.user
        data = request.data
        try:
            folder = Folder.objects.get(id=data["folderId"])
        except Folder.DoesNotExist:
            return Response(
                {"detail": "Folder not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Folder.MultipleObjectsReturned:
            return Response(
                {"detail": "Multiple folders found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except User.MultipleObjectsReturned:
            return Response(
                {"detail": "Multiple users found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Verify request user is creator, or has FULL_ACCESS
        if not source.can_share_folder(folder):
            return Response(
                {"detail": "You do not have permission to share this folder."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if source == target:
            return Response(
                {"detail": "You cannot share a folder with yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # If permission is None, delete the permission
        elif target == folder.creator:
            return Response(
                {"detail": "You cannot modify a creator's access."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif data["permission"] == "none":
            try:
                source.unshare_folder_with_target(folder, target)
                return Response(
                    {"detail": "Permission deleted successfully."},
                    status=status.HTTP_200_OK,
                )
            except FolderPermission.DoesNotExist:
                return Response(
                    {"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            try:
                permission, created = FolderPermission.objects.update_or_create(
                    user=target, folder=folder, permission=data["permission"]
                )
            except FolderPermission.DoesNotExist:
                return Response(
                    {"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND
                )
            except FolderPermission.MultipleObjectsReturned:
                return Response(
                    {"detail": "Multiple shares found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except ValueError:
                return Response(
                    {"detail": "Invalid permission."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"detail": "Folder share successful."},
                status=status.HTTP_200_OK if created else status.HTTP_201_CREATED,
            )


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
