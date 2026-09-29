from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

class PaymentRequest(BaseModel):
    card_number: str = Field(..., min_length=13, max_length=19, example="4111111111111234")
    cardholder_name: str = Field(..., example="Alice Johnson")
    expiration_month: int = Field(..., ge=1, le=12, example=12)
    expiration_year: int = Field(..., ge=2024, le=2040, example=2028)
    cvv: str = Field(..., min_length=3, max_length=4, example="123")
    amount: Decimal = Field(..., gt=0, example=99.50)
    merchant: Optional[str] = Field("Online Store", example="Tech Haven")
    description: Optional[str] = Field("Electronics Purchase", example="USB Adapter")

class PaymentResponse(BaseModel):
    reference_id: str
    status: str
    amount: Decimal
    merchant: str
    card_masked: str
    remaining_balance: Decimal
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    username: Optional[str] = None