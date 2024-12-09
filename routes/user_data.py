from fastapi import APIRouter, HTTPException
from fastapi.templating import Jinja2Templates
from config.db import conn
from fastapi.responses import JSONResponse
from models.model import User, LoginModel, Token, MortgageDetails, AdminToken
from auth.userauth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_admin
from datetime import timedelta
from bson import ObjectId

user = APIRouter()

templates = Jinja2Templates(directory="templates")

@user.post("/register", response_class= JSONResponse)
async def add_user(request: User):
    try:
        print(request)
        user = conn.user.mortgage_details.insert_one(dict(request))
        user_details = {
        "name": request.name,
        "username": request.username,
        "email": request.email,
        "contactnumber": request.contactnumber
        }
        return {"user_details": user_details}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    

@user.post("/login", response_model=Token)
async def login(login_data: LoginModel):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": login_data.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    user_details = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "contactnumber": str(user.get("contactnumber", "")),
    }
    mortgage = {
        "hasMortgage": str(user.get("hasMortgage")),
        "mortgageCount": str(user.get("mortgageCount", "")) if user.get("mortgageCount") is not None else "",
        "resOrBuyToLet": str(user.get("resOrBuyToLet", "")) if user.get("resOrBuyToLet") is not None else "",
        "mortgageType": str(user.get("mortgageType", "")) if user.get("mortgageType") is not None else "",
        "mortgageAmount": str(user.get("mortgageAmount", "")) if user.get("mortgageAmount") is not None else "",
        "renewalDate": str(user.get("renewalDate", "")) if user.get("renewalDate") is not None else "",
        "isLookingForMortgage": str(user.get("isLookingForMortgage")),
        "newMortgageAmount": str(user.get("newMortgageAmount", "")) if user.get("newMortgageAmount") is not None else "",
        "ownershipType": str(user.get("ownershipType", "")) if user.get("ownershipType") is not None else "",
        "depositeAmt": str(user.get("depositeAmt", "")) if user.get("depositeAmt") is not None else "",
        "annualIncome": str(user.get("annualIncome", "")) if user.get("annualIncome") is not None else "",
        "foundProperty": str(user.get("foundProperty")),
        }
    return {"access_token": access_token, "token_type": "bearer", "user_details": user_details, "mortgage": mortgage}

@user.put("/mortgage/{username}")
async def update_mortgage_details(username: str, details: MortgageDetails):
    existing_user = conn.user.mortgage_details.find_one({"username": username})
    print(dict(existing_user))
    if existing_user:
        conn.user.mortgage_details.update_one(
            {"username": username},
            {"$set": details.dict()}
        )
        return {"message": "User data updated successfully!", "data": details}


# Admin

def fetch_all_items(cursor):
    items = list(cursor)
    
    for item in items:
        item["_id"] = str(item["_id"])
    
    return items

@user.get("/users/")
async def read_item():
    print(conn.list_database_names())
    print(conn["user"].list_collection_names())
    data = conn.user.mortgage_details.find({})
    dt = fetch_all_items(data)
    return {"response": dt}

@user.get("/users/{userId}")
async def get_user(userId: str):
    try:
        user_id = ObjectId(userId)
        user = conn.user.mortgage_details.find_one({"_id": user_id})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_dict = dict(user)
        user_dict["_id"] = userId

        return user_dict
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user ID")

@user.post("/admin/login", response_model=AdminToken)
async def login(login_data: LoginModel):
    admin = authenticate_admin(login_data.username, login_data.password)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": login_data.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    admin_details = {
        "id": str(admin["_id"]),
        "username": admin["username"],
        "email": admin.get("email", ""),
        "name": admin.get("name", ""),
        "contactnumber": str(admin.get("contactnumber", "")),
    }
    return {"access_token": access_token, "token_type": "bearer", "admin_details": admin_details}