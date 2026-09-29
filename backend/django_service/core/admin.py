from django.contrib import admin
from .models import CreditCard, PaymentTransaction

@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'cardholder_name', 'masked_card', 'available_balance', 'credit_limit', 'is_active', 'created_at')
    search_fields = ('cardholder_name', 'card_number')
    list_filter = ('is_active',)

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_id', 'card', 'amount', 'merchant', 'status', 'timestamp')
    list_filter = ('status', 'merchant')
    search_fields = ('reference_id',)