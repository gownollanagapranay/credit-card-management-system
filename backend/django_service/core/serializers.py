import hashlib
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CreditCard, PaymentTransaction

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        # Uses Django's PBKDF2 with SHA-256 for secure password hashing
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

class CreditCardCreateSerializer(serializers.Serializer):
    cardholder_name = serializers.CharField(max_length=100)
    card_number = serializers.CharField(write_only=True, min_length=13, max_length=19)
    expiration_month = serializers.IntegerField(min_value=1, max_value=12)
    expiration_year = serializers.IntegerField(min_value=2024, max_value=2040)
    cvv = serializers.CharField(write_only=True, min_length=3, max_length=4)
    credit_limit = serializers.DecimalField(max_digits=12, decimal_places=2, default=5000.00)

    def create(self, validated_data):
        raw_number = validated_data.pop('card_number').replace(' ', '').replace('-', '')
        raw_cvv = validated_data.pop('cvv')
        
        last_4 = raw_number[-4:]
        masked = f"****-****-****-{last_4}"
        card_hash = hashlib.sha256(raw_number.encode('utf-8')).hexdigest()
        cvv_hash = hashlib.sha256(raw_cvv.encode('utf-8')).hexdigest()

        return CreditCard.objects.create(
            user=self.context['request'].user,
            cardholder_name=validated_data['cardholder_name'],
            masked_card=masked,
            last_4=last_4,
            card_hash=card_hash,
            cvv_hash=cvv_hash,
            expiration_month=validated_data['expiration_month'],
            expiration_year=validated_data['expiration_year'],
            credit_limit=validated_data.get('credit_limit', 5000.00),
            available_balance=validated_data.get('credit_limit', 5000.00),
        )

class CreditCardReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ['id', 'cardholder_name', 'masked_card', 'last_4', 'expiration_month', 'expiration_year', 'available_balance', 'credit_limit', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    card_display = serializers.CharField(source='card.masked_card', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = ['id', 'reference_id', 'amount', 'merchant', 'status', 'message', 'card_display', 'timestamp']