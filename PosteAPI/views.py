from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

# import local data
from .serializers import UserCreateSerializer, UserLoginSerializer, UserSerializer

# Create views / viewsets here.


class UserAPI(APIView):
    @swagger_auto_schema(
        responses={
            200: UserSerializer(many=True),
            400: "Bad Request",
        },
    )
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserCreateSerializer,
        responses={
            200: UserSerializer(many=False),
            400: "Bad Request",
        },
    )
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data["username"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
            response = Response(
                UserSerializer(user).data, status=status.HTTP_201_CREATED
            )
            print(response)
            return response
        else:
            print(serializer.errors)
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            print(response)
            return response


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


class UserLogin(APIView):
    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        responses={
            200: UserSerializer(many=False),
            400: "Bad Request",
            401: "Invalid email or password",
        },
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            password = serializer.validated_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user:
                # User authenticated successfully
                serializer = UserSerializer(user)
                return Response(
                    {"result": {"success": True, "user": serializer.data}},
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
