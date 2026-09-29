from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.sql import func
from .database import Base

class CreditCard(Base):
    __tablename__ = "core_creditcard"

    id = Column(Integer, primary_key=True, index=True)
    cardholder_name = Column(String(100), nullable=False)
    card_number = Column(String(16), unique=True, nullable=False, index=True)
    expiration_month = Column(Integer, nullable=False)
    expiration_year = Column(Integer, nullable=False)
    cvv = Column(String(4), nullable=False)
    credit_limit = Column(Numeric(12, 2), nullable=False, default=5000.00)
    available_balance = Column(Numeric(12, 2), nullable=False, default=5000.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)

class PaymentTransaction(Base):
    __tablename__ = "core_paymenttransaction"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    merchant = Column(String(100), nullable=False, default="General Merchant")
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    reference_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    card_id = Column(Integer, ForeignKey("core_creditcard.id"), nullable=False)