from fastapi import APIRouter, HTTPException, Request
from utils.logging import logger
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Optional
import jwt

from settings.env import GOOGLE_CLIENT_ID, JWT_SECRET, JWT_ALGORITHM

router = APIRouter()

# You'll need to set these environment variables

@router.post("/auth/google")
async def google_auth(request: Request):
    try:
        # Get the token from request body
        data = await request.json()
        token = data.get("token")
        
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        # Verify the Google token
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), GOOGLE_CLIENT_ID
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
                
            # Extract user info
            user_id = idinfo['sub']
            email = idinfo['email']
            name = idinfo.get('name')
            picture = idinfo.get('picture')
            
            # Here you would typically:
            # 1. Check if user exists in your database
            # 2. If not, create new user
            # 3. If yes, update last login
            
            # For now, we'll just create a JWT token
            token_data = {
                "sub": user_id,
                "email": email,
                "name": name,
                "exp": datetime.utcnow() + timedelta(days=1)
            }
            
            access_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
            
            return {
                "status": "success",
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "picture": picture
                }
            }
            
        except ValueError as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")
