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

# @user.post("/register", response_class=JSONResponse)
# async def add_user(request: User):
#     try:
        
#         request.username = request.username.lower()
#         user = conn.user.mortgage_details.insert_one(dict(request))
        
#         user_details = {
#             "name": request.name,
#             "username": request.username.lower(),
#             "email": request.email,
#             "contactnumber": request.contactnumber
#         }
        
#         return {"user_details": user_details}
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    

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
        "isLookingForMortgage": str(user.get("isLookingForMortgage")),
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

@user.get("/counts")
async def get_counts():
    # Total entries count
    total_count = conn.user.mortgage_details.count_documents({})

    has_mortgage_count = conn.user.mortgage_details.count_documents({"hasMortgage": True})

    is_looking_for_mortgage_count = conn.user.mortgage_details.count_documents({"isLookingForMortgage": True})

    return {
        "total_count": total_count,
        "has_mortgage_count": has_mortgage_count,
        "is_looking_for_mortgage_count": is_looking_for_mortgage_count,
    }

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