from fastapi import APIRouter, HTTPException
from utils.logging import logger
from bson import ObjectId

from database.mongodb import db

router = APIRouter()

@router.get("/profile/{user_id}", response_model=dict)
async def get_user_profile(user_id: str):
    try:
        # Validate user_id format
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Get user from database
        user = await db['users'].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Convert ObjectId to string for serialization
        user['id'] = str(user.pop('_id'))

        # If user has active subscription, get subscription details
        subscription_details = None
        subscription_plan = None
        if user.get('active_subscription_id'):
            subscription = await db['subscriptions'].find_one(
                {"_id": ObjectId(user['active_subscription_id'])}
            )
            if subscription:
                subscription['id'] = str(subscription.pop('_id'))
                subscription_details = subscription

                # Get subscription plan details
                plan = await db['subscription_plans'].find_one(
                    {"_id": ObjectId(subscription['plan_id'])}
                )
                if plan:
                    plan['id'] = str(plan.pop('_id'))
                    subscription_plan = plan

        return {
            "status": "success",
            "user": user,
            "subscription": subscription_details,
            "subscription_plan": subscription_plan
        }

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
