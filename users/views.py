from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'error': 'Hem e-posta hem şifre gereklidir.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Geçersiz e-posta veya şifre.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyPasswordView(APIView):
    """
    Mevcut oturumu bozmadan sadece şifre doğrular.
    Gizli sekme unlock işlemi için kullanılır.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Şifre gereklidir.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=request.user.email, password=password)
        if user is not None:
            return Response({'valid': True}, status=status.HTTP_200_OK)
        return Response({'valid': False}, status=status.HTTP_200_OK)
