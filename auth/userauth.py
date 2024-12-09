from config.db import conn
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("password")

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username: str, password: str):
    user = conn.user.mortgage_details.find_one({"username": username})
    if not user:
        return False
    # If user password is plaintext, hash it (not recommended for production)
    hashed_password = pwd_context.hash(user["password"]) if "hashed_password" not in user else user["hashed_password"]
    print(password, hashed_password)
    if not verify_password(password, hashed_password):
        return False
    return user


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