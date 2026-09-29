import os
import datetime
import jwt
from pathlib import Path
from dotenv import load_dotenv

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import CreditCard, PaymentTransaction
from .serializers import (
    RegisterSerializer,
    CreditCardCreateSerializer,
    CreditCardReadSerializer,
    TransactionSerializer
)

load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / '.env')
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def generate_jwt(user: User) -> str:
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user = User.objects.get(id=payload['user_id'])
            return (user, None)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            raise AuthenticationFailed('Invalid or expired JWT token.')

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_jwt(user)
            return Response({"message": "User registered successfully", "token": token, "username": user.username}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token = generate_jwt(user)
            return Response({"message": "Login successful", "token": token, "username": user.username}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials provided."}, status=status.HTTP_401_UNAUTHORIZED)

class CardListCreateView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cards = CreditCard.objects.filter(user=request.user, is_active=True).order_by('-created_at')
        return Response(CreditCardReadSerializer(cards, many=True).data)

    def post(self, request):
        serializer = CreditCardCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            card = serializer.save()
            return Response(CreditCardReadSerializer(card).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CardDeleteView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            card = CreditCard.objects.get(pk=pk, user=request.user)
            card.is_active = False # Safe soft-delete to preserve audit logs
            card.save()
            return Response({"message": "Card deleted successfully"}, status=status.HTTP_200_OK)
        except CreditCard.DoesNotExist:
            return Response({"error": "Card not found"}, status=status.HTTP_404_NOT_FOUND)

class TransactionListView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        txns = PaymentTransaction.objects.filter(user=request.user).order_by('-timestamp')
        return Response(TransactionSerializer(txns, many=True).data)