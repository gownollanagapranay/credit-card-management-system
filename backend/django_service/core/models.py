import hashlib
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    cardholder_name = models.CharField(max_length=100)
    # PCI DSS Compliance: Store only masked card representation and last 4 digits
    masked_card = models.CharField(max_length=24) # e.g. ****-****-****-1234
    last_4 = models.CharField(max_length=4)
    # Deterministic SHA-256 hash to identify the card during transactions without storing plaintext
    card_hash = models.CharField(max_length=64, unique=True, db_index=True)
    cvv_hash = models.CharField(max_length=64)
    expiration_month = models.IntegerField()
    expiration_year = models.IntegerField()
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('5000.00'))
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('5000.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def hash_value(val: str) -> str:
        return hashlib.sha256(val.strip().encode('utf-8')).hexdigest()

    def __str__(self):
        return f"{self.cardholder_name} ({self.masked_card})"

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    merchant = models.CharField(max_length=100, default='General Merchant')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reference_id = models.CharField(max_length=64, unique=True, db_index=True)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference_id} - {self.amount} ({self.status})"