from fastapi import APIRouter, HTTPException, Request, Depends
from utils.logging import logger
from datetime import datetime, timedelta
from typing import Optional
import hmac
import hashlib

from settings.env import RAZORPAY_WEBHOOK_SECRET
from database.mongodb import db
from models.subscription import Payment, Subscription, SubscriptionStatus, PaymentStatus

router = APIRouter()

def verify_razorpay_signature(request_body: bytes, signature: str, webhook_secret: str) -> bool:
    expected_signature = hmac.new(
        webhook_secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    try:
        # Get the raw request body
        body = await request.body()
        
        # Verify webhook signature
        signature = request.headers.get("x-razorpay-signature")
        if not signature or not verify_razorpay_signature(body, signature, RAZORPAY_WEBHOOK_SECRET):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse webhook data
        payload = await request.json()
        event = payload.get("event")

        if event == "payment.captured":
            payment_data = payload.get("payload", {}).get("payment", {})
            
            # Extract payment details
            payment = {
                "razorpay_payment_id": payment_data.get("id"),
                "razorpay_order_id": payment_data.get("order_id"),
                "amount": float(payment_data.get("amount")) / 100,  # Convert from paise to rupees
                "currency": payment_data.get("currency"),
                "status": PaymentStatus.SUCCESS,
                "payment_method": payment_data.get("method"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Get subscription details from metadata
            metadata = payment_data.get("notes", {})
            user_id = metadata.get("user_id")
            plan_id = metadata.get("plan_id")
            
            if not user_id or not plan_id:
                raise HTTPException(status_code=400, detail="Missing user_id or plan_id in payment metadata")

            # Get plan details
            plan = await db['subscription_plans'].find_one({"_id": plan_id})
            if not plan:
                raise HTTPException(status_code=404, detail="Subscription plan not found")

            # Create subscription
            subscription = {
                "user_id": user_id,
                "plan_id": plan_id,
                "status": SubscriptionStatus.ACTIVE,
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=plan["duration_days"]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Save subscription
            subscription_result = await db['subscriptions'].insert_one(subscription)
            subscription_id = str(subscription_result.inserted_id)

            # Update payment with subscription_id
            payment["subscription_id"] = subscription_id
            payment["user_id"] = user_id
            await db['payments'].insert_one(payment)

            # Update user's active subscription
            await db['users'].update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "active_subscription_id": subscription_id,
                        "subscription_status": SubscriptionStatus.ACTIVE,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            return {"status": "success"}

    except Exception as e:
        logger.error(f"Razorpay webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))