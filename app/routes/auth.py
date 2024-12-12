from fastapi import APIRouter, HTTPException
from utils.logging import logger
from datetime import datetime, timedelta
import jwt
import bcrypt

from settings.env import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRES_IN
from database.mongodb import db
from models.user import User, UserInDB, UserSignup, UserLogin

router = APIRouter()

async def get_user_by_email(email: str):
    user = await db['users'].find_one({"email": email})
    if user:
        return UserInDB(**user)
    return None

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

async def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

@router.post("/signup", response_model=User)
async def signup(user: UserSignup):
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )

        # Hash the password
        hashed_password = await get_password_hash(user.password)
        
        # Create user document
        user_dict = {
            "name": user.name,
            "email": user.email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into database
        result = await db['users'].insert_one(user_dict)
        
        # Create JWT token
        token_data = {
            "sub": str(result.inserted_id),
            "email": user.email,
            "name": user.name,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        
        access_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "status": "success",
            "message": "User created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(result.inserted_id),
                "email": user.email,
                "name": user.name
            }
        }
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    try:
        # Verify user exists
        db_user = await get_user_by_email(user.email)
        if not db_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # Verify password
        if not await verify_password(user.password, db_user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # Generate token
        token_data = {
            "sub": str(db_user.id),
            "email": db_user.email,
            "name": db_user.name,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        
        access_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(db_user.id),
                "email": db_user.email,
                "name": db_user.name
            }
        }
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

