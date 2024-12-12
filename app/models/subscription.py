from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class PlanType(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"

class SubscriptionPlan(BaseModel):
    id: str
    name: str
    type: PlanType
    price: float
    duration_days: int
    description: str
    features: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Subscription(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class Payment(BaseModel):
    id: str
    user_id: str
    subscription_id: str
    razorpay_payment_id: str
    razorpay_order_id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 