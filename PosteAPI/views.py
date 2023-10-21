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

from .models import User, Folder, FolderPermission

# import local data
from .serializers import UserCreateSerializer, UserLoginSerializer, UserSerializer, FolderSerializer


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

    def update(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        folder = Folder.objects.get(['folder_id'])
        if not user.can_share_folder(folder):
            return Response({"detail": "You do not have permission to share this folder."},
                            status=status.HTTP_403_FORBIDDEN)

        permission, created = FolderPermission.objects.get_or_create(
            user=User.objects.get(data['user_id']),
            folder=folder,
            # @TODO verify if I need to do any type casting
            permission=data['permission']
        )

        # If the permission already exists, update it
        if not created:
            permission.permission = data['permission']
            permission.save()

        return Response({"detail": "Permission upsert successfully."},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


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


class FolderDetail(APIView):
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
