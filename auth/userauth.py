from fastapi import Depends, HTTPException, status
from config.db import conn
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import bcrypt

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("password")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # Endpoint to get tokens (implement this if not already)



def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def authenticate_user(username: str, password: str):
    # Fetch user from the database
    user = conn.user.mortgage_details.find_one({"username": username})
    if not user:
        return None
    
    # Verify the password
    if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return None
    
    return user

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def authenticate_admin(username: str, password: str):
    admin = conn.user.admin_details.find_one({"username": username})
    if not admin:
        return False
    # If user password is plaintext, hash it (not recommended for production)
    hashed_password = pwd_context.hash(admin["password"]) if "hashed_password" not in admin else admin["hashed_password"]
    print(password, hashed_password)
    if not verify_password(password, hashed_password):
        return False
    return admin

def create_reset_token(user_id: str):
    """
    Generate a JWT token for password reset.
    """
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token