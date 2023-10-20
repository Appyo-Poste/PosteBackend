import http

from django.contrib.auth import authenticate
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .models import User, Folder, Post, FolderPermission

# import local data
from .serializers import UserCreateSerializer, UserLoginSerializer, UserSerializer, FolderSerializer, \
    FolderCreateSerializer, PostCreateSerializer, PostSerializer, FolderPermissionSerializer


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
                }
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

    def get_queryset(self):
        user = self.request.user
        folder_permissions = FolderPermission.objects.filter(user=user).exclude(permission__isnull=True).select_related(
            'folder')
        permitted_folders_ids = [perm.folder.id for perm in folder_permissions]
        folders = Folder.objects.filter(Q(creator=user) | Q(id__in=permitted_folders_ids)).distinct()
        return folders

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = {'request': request, 'user_permissions': self.get_user_permissions(request.user, queryset)}
        serializer = self.get_serializer(queryset, many=True, context=context)
        return Response(serializer.data)

    def get_user_permissions(self, user, folders):
        folder_permissions = FolderPermission.objects.filter(user=user, folder__in=folders)
        # Create a dictionary with folder IDs as keys and permissions as values.
        permissions_dict = {perm.folder_id: perm.permission for perm in folder_permissions}
        return permissions_dict

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
            user = serializer.save()
            response = Response(status=status.HTTP_201_CREATED)
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
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


class FolderAPI(APIView):
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
            folder = serializer.save()
            response = Response(
                FolderSerializer(folder).data, status=status.HTTP_201_CREATED
            )
            return response
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
                {"error": "User does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND
            )

        owned_folders = self.get_owned(user)
        shared_folders = self.get_shared(user)
        folders = None

        if owned_folders is None and shared_folders is None:
            return Response(
                {"error": "User has no folders", "success": False}, status=status.HTTP_404_NOT_FOUND
            )
        elif owned_folders is None:
            folders = shared_folders
        elif shared_folders is None:
            folders = owned_folders
        else:
            folders = shared_folders | owned_folders

        serializer = FolderSerializer(folders, many=True)
        return Response({"success": True,"folders": serializer.data}, status=status.HTTP_200_OK)


class PostAPI(APIView):
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
    def post(self, request):

        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save()
            response = Response(
                PostSerializer(post).data, status=status.HTTP_201_CREATED
            )
            return response
        else:
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            # error message contained in response.data
            return response


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
                {"error": "folder does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND
            )

        post = self.get_post(pk2)
        if post is None:
            return Response(
                {"error": "post does not exist", "success": False}, status=status.HTTP_404_NOT_FOUND
            )

        post.folder = folder
        post.save()

        return Response({"success": True}, status=status.HTTP_200_OK)


class deleteFolder(APIView):
    def get_object(self, pk):
        try:
            return Folder.objects.get(pk=pk)
        except Folder.DoesNotExist:
            return None

    def get(self, request, pk):
        folder = self.get_object(pk)
        if folder is not None:
            folder.delete()
            return Response({"success": True}, status=status.HTTP_200_OK)
        else:
            return Response({"success": False, "Error": "folder does not exist."}, status=status.HTTP_400_BAD_REQUEST)
