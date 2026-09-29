import os
import uuid
import hashlib
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Environment Resolution
env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secure-shared-jwt-secret-key-for-django-and-fastapi-32bytes")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "RootPassword123!")
DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "credit_card_payment_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models mapping to Django's tables
class CreditCard(Base):
    __tablename__ = "core_creditcard"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    cardholder_name = Column(String(100))
    masked_card = Column(String(24))
    last_4 = Column(String(4))
    card_hash = Column(String(64), unique=True)
    cvv_hash = Column(String(64))
    expiration_month = Column(Integer)
    expiration_year = Column(Integer)
    available_balance = Column(Numeric(12, 2))
    is_active = Column(Boolean, default=True)

class PaymentTransaction(Base):
    __tablename__ = "core_paymenttransaction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    card_id = Column(Integer, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    merchant = Column(String(100), default="General Merchant")
    status = Column(String(10), default="PENDING")
    reference_id = Column(String(64), unique=True)
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

app = FastAPI(title="FastAPI Payment Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user_id claim")
        return int(user_id)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"JWT validation error: {str(e)}")

class PaymentInput(BaseModel):
    card_number: str = Field(..., example="4111222233334444")
    cardholder_name: str = Field(..., example="John Doe")
    expiration_month: int = Field(..., ge=1, le=12, example=12)
    expiration_year: int = Field(..., ge=2024, le=2040, example=2028)
    cvv: str = Field(..., min_length=3, max_length=4, example="123")
    amount: Decimal = Field(..., gt=0, example=150.00)
    merchant: str = Field("General Merchant", example="Amazon Online")

@app.post("/api/payments/pay")
def process_payment(
    data: PaymentInput,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        ref_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        raw_num = data.card_number.replace(' ', '').replace('-', '')
        c_hash = hashlib.sha256(raw_num.encode('utf-8')).hexdigest()
        v_hash = hashlib.sha256(data.cvv.strip().encode('utf-8')).hexdigest()

        # Step 1: Look up card
        card = db.query(CreditCard).filter(
            CreditCard.card_hash == c_hash,
            CreditCard.user_id == user_id,
            CreditCard.is_active == True
        ).first()

        # Step 2: Initialize Payment Record in PENDING status
        txn = PaymentTransaction(
            user_id=user_id,
            card_id=card.id if card else None,
            amount=data.amount,
            merchant=data.merchant,
            status="PENDING",
            reference_id=ref_id,
            message="Payment initialized and awaiting verification."
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)

        # Step 3: Validate Card Existence & Active Status
        if not card:
            txn.status = "FAILED"
            txn.message = "Transaction Failed: Card does not exist, belongs to another user, or is inactive."
            db.commit()
            return {"reference_id": ref_id, "status": "FAILED", "reason": txn.message}

        # Step 4: Validate Expiration and CVV
        if (int(card.expiration_month) != int(data.expiration_month) or 
            int(card.expiration_year) != int(data.expiration_year) or 
            str(card.cvv_hash).strip() != str(v_hash).strip()):
            txn.status = "FAILED"
            txn.message = "Transaction Failed: Invalid CVV or Expiration date."
            db.commit()
            return {"reference_id": ref_id, "status": "FAILED", "reason": txn.message}

        # Step 5: Validate Balance
        if Decimal(str(card.available_balance)) < data.amount:
            txn.status = "FAILED"
            txn.message = "Transaction Failed: Insufficient balance/credit limit."
            db.commit()
            return {"reference_id": ref_id, "status": "FAILED", "reason": txn.message}

        # Step 6: Settle Payment - Deduct Balance & set status to SUCCESS
        card.available_balance = Decimal(str(card.available_balance)) - data.amount
        txn.status = "SUCCESS"
        txn.message = "Transaction Settled Successfully."
        db.commit()

        return {
            "reference_id": ref_id,
            "status": "SUCCESS",
            "amount": float(data.amount),
            "merchant": data.merchant,
            "masked_card": card.masked_card,
            "remaining_balance": float(card.available_balance),
            "message": txn.message
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment execution error: {str(exc)}"
        )