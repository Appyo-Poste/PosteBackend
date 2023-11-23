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
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Folder, FolderPermissionEnum, Post, Share, User

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


def get_permission_level(permission):
    levels = {
        None: 0,
        FolderPermissionEnum.VIEWER: 1,
        FolderPermissionEnum.EDITOR: 2,
        FolderPermissionEnum.FULL_ACCESS: 3,
    }
    return levels.get(permission, 0)


def get_highest_permission(user, folder):
    highest_permission = None
    shares = Share.objects.filter(target=user, folder=folder)
    for share in shares:
        permission = share.permission
        if get_permission_level(permission) > get_permission_level(highest_permission):
            highest_permission = permission

    return highest_permission


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

    def get_queryset(self):
        user = self.request.user1
        folders = Folder.objects.filter(
            Q(creator=user)
            | Q(  # Folders owned by the user
                share__target=user, share__permission__isnull=False
            )
            # Folders shared with the user with a valid permission
        ).distinct()
        return folders

    @swagger_auto_schema(manual_parameters=[token_param])
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        folders = self.get_queryset()
        context = {
            "request": request,
            "user_permissions": self.get_user_permissions(request.user1, folders),
            "shared_users": self.get_shared_users(request.user1, folders),
        }
        serializer = self.get_serializer(folders, many=True, context=context)
        return Response(serializer.data)

    def get_shared_users(self, request_user, folders):
        """
        Return a dictionary mapping folders to lists of user emails with whom the
        folder is shared.
        If the request user does not have FULL_ACCESS to the folder, the folder will
        include no shared users.

        This is because only those users with FULL_ACCESS can share folders,
        and therefore only those users can change the shared users list.

        The request user's email will always be excluded.

        Key:   folder_id
        Value: list of user emails
        """
        shared_user_dict = {}
        for folder in folders:
            shared = (
                Share.objects.filter(source=request_user, folder=folder)
                .exclude(target=request_user)
                .values_list("target__email", flat=True)
            )
            shared_user_dict[folder.id] = list(set(list(shared)))
        return shared_user_dict

    def get_user_permissions(self, user, folders):
        """
        Return a dictionary mapping folders to permissions for the given user.
        Key:    folder_id
        Value:  permission
        """
        perm_dict = {}
        for folder in folders:
            if folder.creator == user:
                perm_dict[folder.id] = FolderPermissionEnum.FULL_ACCESS
            else:
                highest_permission = get_highest_permission(user, folder)
                perm_dict[folder.id] = highest_permission
        return perm_dict

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
        source = request.user1
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

        # If permission is None, delete the permission
        if data["permission"] == "none":
            try:
                source.unshare_folder_with_target(folder, target)
                return Response(
                    {"detail": "Permission deleted successfully."},
                    status=status.HTTP_200_OK,
                )
            except Share.DoesNotExist:
                return Response(
                    {"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND
                )
            except Share.MultipleObjectsReturned:
                return Response(
                    {"detail": "Multiple shares found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Update existing or create - unique by source, target, folder
            permission, created = Share.objects.update_or_create(
                source=source,
                target=target,
                folder=folder,
                permission=data["permission"],
            )
            return Response(
                {"detail": "Permission upserted successfully."},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
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
            Folder.objects.create(creator=request.user1, **validated_data)
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
        shared = Share.objects.filter(
            target=user, permission__isnull=False
        ).values_list("folder", flat=True)
        return shared

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
        serializer = PostCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.validated_data["creator"] = request.user1
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return response


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

    def patch(self, request, id):
        """
        Edits a post in the server
        :param request: Request object with post id and auth in header
                        Request Body contains new title, description and url
        """
        try:
            post = Post.objects.get(pk=id)
            data = json.loads(request.body.decode("utf-8"))
            post.edit(data.get("title"), data.get("description"), data.get("url"))
            return Response({"success": True}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            message = "Post does not exist"
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            message = "Server error occurred while deleting post"
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class addPostToFolder(APIView):
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
        except Exception:
            message = "Server error occurred while editing folder"
            return Response(
                {"success": False, "errors": {"post": [message]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
