from fastapi import APIRouter, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from models.model import *
from auth.userauth import *
from datetime import timedelta
from bson import ObjectId
from typing import List
import smtplib
from config.db import email_address, email_password
from jose import jwt, JWTError
from email.message import EmailMessage
from schemas.schema import *
from pymongo import MongoClient
from config.db import MONGO_URL

conn = MongoClient(MONGO_URL)
user = APIRouter()

templates = Jinja2Templates(directory="templates")

############################### USER REGISTRATION ################################
@user.post("/register", response_class=JSONResponse)
async def add_user(request: User):
    try:
        request.username = request.username.lower()

        existing_user_by_username = conn.user.mortgage_details.find_one({"username": request.username})
        if existing_user_by_username:
            raise HTTPException(status_code=400, detail="Username already exists.")
        
        existing_user_by_email = conn.user.mortgage_details.find_one({"email": request.email})
        if existing_user_by_email:
            raise HTTPException(status_code=400, detail="Email already exists.")

        # Insert the new user
        user = conn.user.mortgage_details.insert_one(dict(request))
        
        # Prepare the user details response
        user_details = {
            "name": request.name,
            "username": request.username,
            "email": request.email,
            "contactnumber": request.contactnumber
        }
        msg = EmailMessage()

        msg["Subject"] = "Registration Successful"
        msg["From"] = email_address
        msg["To"] = request.email
        msg.set_content(
            f"""\
                Name: {request.name}
                Email: {request.email}
                
                Dear {request.username},

                Congratulations! Your registration has been successfully completed.

                Thank you for joining us. We're excited to have you on board. If you have any questions or need assistance, feel free to contact our support team.\n

                Best regards,
                AAI Financials
                {email_address}
            """
        )

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)

        return {"user_details": user_details}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


################################ USER LOGIN #####################################
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


################################# ADD RESPONSE #######################################
@user.post("/add_mortgage_data/")
async def add_mortgage_data(data: MortgageDetails):
    try:
        user_doc = conn.user.mortgage_details.find_one({"username": data.username})
        
        if data.hasMortgage:
            entry = {
                "_id": ObjectId(),
                "hasMortgage": data.hasMortgage,
                "paymentMethod": data.paymentMethod,
                "estPropertyValue": data.estPropertyValue,
                "mortgageAmount": data.mortgageAmount,
                "loanToValue1": data.loanToValue1,
                "furtherAdvance": data.furtherAdvance,
                "mortgageType": data.mortgageType,
                "productRateType": data.productRateType,
                "renewalDate": data.renewalDate,
                'reference1': data.reference1,
            }
            # Append to mortgage_details array
            conn.user.mortgage_details.update_one(
                {"username": data.username},
                {"$push": {"mortgage_details": entry}}
            )
        else:
            entry = {
                "_id": ObjectId(),
                "isLookingForMortgage": data.isLookingForMortgage,
                "foundProperty": data.foundProperty,
                "newMortgageType": data.newMortgageType,
                "depositAmount": data.depositAmount,
                "purchasePrice": data.purchasePrice,
                "loanToValue2": data.loanToValue2,
                "loanAmount": data.loanAmount,
                "sourceOfDeposit": data.sourceOfDeposit,
                "loanTerm": data.loanTerm,
                "newPaymentMethod": data.newPaymentMethod,
                'reference2': data.reference2
            }
            # Append to new_mortgage_requests array
            conn.user.mortgage_details.update_one(
                {"username": data.username},
                {"$push": {"new_mortgage_requests": entry}}
            )
        
        return {"message": "Data added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Admin

############################### MyClients.js #################################
@user.get("/users", response_model=List[AllUser])
async def get_all_users():
    users = conn.user.mortgage_details.find({})
    all_users = fetch_all_items(users)
    return serialize_mongo_document(all_users)


############################### RESPONSE #################################### 
@user.get("/user/{username}")
async def get_user(username: str):
    try:
        user = conn.user.mortgage_details.find_one({"username": username})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        user = serialize_document(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user ID")

############################### ADMIN LOGIN ####################################
@user.post("/admin/login", response_model=AdminToken)
async def login(login_data: LoginModel):
    username = login_data.username
    admin = authenticate_admin(username.lower(), login_data.password)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": login_data.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    admin_details = {
        "id": str(admin["_id"]),
        "username": admin["username"],
        "email": admin.get("email", ""),
        "name": admin.get("name", ""),
        "contactnumber": str(admin.get("contactnumber", "")),
    }
    return {"access_token": access_token, "token_type": "bearer", "admin_details": admin_details}

############################### DELETE RESPONSE #######################################

@user.delete("/delete-response/{response_id}")
async def delete_response(response_id: str, type: str):
    collection = "mortgage_details" if type == "existing" else "new_mortgage_requests"
    result = conn.user.mortgage_details.update_one(
        {collection: {"$elemMatch": {"_id": ObjectId(response_id)}}},
        {"$pull": {collection: {"_id": ObjectId(response_id)}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Response not found")
    return {"message": "Response deleted successfully"}


################################ COUNTS #############################################

@user.get("/count_mortgages")
async def count_mortgages():
    has_mortgage_count = conn.user.mortgage_details.aggregate([
        {"$unwind": "$mortgage_details"},
        {"$match": {"mortgage_details.hasMortgage": True}},
        {"$count": "has_mortgage_count"}
    ])

    has_mortgage_count = list(has_mortgage_count)
    has_mortgage_count = has_mortgage_count[0]["has_mortgage_count"] if has_mortgage_count else 0

    looking_for_mortgage_count = conn.user.mortgage_details.aggregate([
        {"$unwind": "$new_mortgage_requests"},
        {"$match": {"new_mortgage_requests.isLookingForMortgage": True}},
        {"$count": "looking_for_mortgage_count"}
    ])

    looking_for_mortgage_count = list(looking_for_mortgage_count)
    looking_for_mortgage_count = looking_for_mortgage_count[0]["looking_for_mortgage_count"] if looking_for_mortgage_count else 0

    total_count = conn.user.mortgage_details.count_documents({})
    return JSONResponse(content={
        "total_count": total_count,
        "has_mortgage_count": has_mortgage_count,
        "looking_for_mortgage_count": looking_for_mortgage_count
    })

########################## UPDATING DATA #############################

@user.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate):
    existing_user_by_username = conn.user.mortgage_details.find_one({"username": user_data.username})
    
    object_id = ObjectId(user_id)
    result = conn.user.mortgage_details.update_one(
        {"_id": object_id},
        {"$set": user_data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}


@user.put("/update-mortgage/{user_id}")
async def update_mortgage(user_id: str, mortgage: ExistingMortgageDetails):
    user = conn.user.mortgage_details.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build the update payload dynamically
    update_payload = {
        "mortgage_details.$.hasMortgage": mortgage.hasMortgage,
        "mortgage_details.$.paymentMethod": mortgage.paymentMethod,
        "mortgage_details.$.estPropertyValue": mortgage.estPropertyValue,
        "mortgage_details.$.mortgageAmount": mortgage.mortgageAmount,
        "mortgage_details.$.loanToValue1": mortgage.loanToValue1,
        "mortgage_details.$.furtherAdvance": mortgage.furtherAdvance,
        "mortgage_details.$.mortgageType": mortgage.mortgageType,
        "mortgage_details.$.productRateType": mortgage.productRateType,
        "mortgage_details.$.renewalDate": mortgage.renewalDate,
        "mortgage_details.$.reference1": mortgage.reference1,
    }

    updated = conn.user.mortgage_details.update_one(
        {"_id": ObjectId(user_id), "mortgage_details._id": ObjectId(mortgage.id)},
        {"$set": update_payload},
    )

    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mortgage details not found")

    return {"message": "Mortgage details updated successfully"}


@user.put("/update-new-mortgage/{user_id}")
async def update_mortgage(user_id: str, mortgage: NewMortgageRequest):
    user = conn.user.mortgage_details.find_one({"_id": ObjectId(user_id)})
    print(user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = conn.user.mortgage_details.update_one(
        {"_id": ObjectId(user_id), "new_mortgage_requests._id": ObjectId(mortgage.id)},
        {
            "$set": {
                "new_mortgage_requests.$.isLookingForMortgage": mortgage.isLookingForMortgage,
                "new_mortgage_requests.$.newMortgageType": mortgage.newMortgageType,
                "new_mortgage_requests.$.foundProperty": mortgage.foundProperty,
                "new_mortgage_requests.$.depositAmount": mortgage.depositAmount,
                "new_mortgage_requests.$.purchasePrice": mortgage.purchasePrice,
                "new_mortgage_requests.$.loanToValue2": mortgage.loanToValue2,
                "new_mortgage_requests.$.loanAmount": mortgage.loanAmount,
                "new_mortgage_requests.$.sourceOfDeposit": mortgage.sourceOfDeposit,
                "new_mortgage_requests.$.loanTerm": mortgage.loanTerm,
                "new_mortgage_requests.$.newPaymentMethod": mortgage.newPaymentMethod,
                "new_mortgage_requests.$.reference2": mortgage.reference2,
            }
        },
    )

    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mortgage details not found")
    
    return {"message": "Mortgage details updated successfully"}


########################## FORGOT PASSWORD #############################

def send_email(to_email: str, reset_link: str):
    """
    Send the password reset link via email.
    """
    msg = EmailMessage()

    msg["Subject"] = "Reset Your Password"
    msg["From"] = email_address
    msg["To"] = to_email
    msg.set_content(f"""
    Hello,

    You requested to reset your password. Click the link below to reset it:
    {reset_link}

    This link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes.

    If you did not request a password reset, please ignore this email.

    Best regards,
    Your App Team
    """)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)

@user.post("/password-reset-request")
async def password_reset_request(request: PasswordResetRequest):
    email = request.email
    user = conn.user.mortgage_details.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user["_id"])
    token = create_reset_token(user_id)
    reset_link = f"https://darkslategray-barracuda-138975.hostingersite.com/reset-password?token={token}"
    send_email(email, reset_link)

    return {"message": "Password reset link sent successfully."}
    

@user.post("/password-change")
async def password_change(change_request: PasswordChangeRequest):
    token = change_request.token
    new_password = change_request.new_password

    try:
        # Decode token to get the username
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        userID: str = payload.get("sub")
        if userID is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Find user and update password
    user = conn.user.mortgage_details.find_one({"_id": ObjectId(userID)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash the new password and update it in the database
    hashed_password = pwd_context.hash(new_password)
    conn.user.mortgage_details.update_one(
        {"_id": ObjectId(userID)}, {"$set": {"password": new_password}}
    )

    return {"message": "Password has been updated successfully."}

################################ DELETE USER ###################################

@user.delete("/users/delete/{user_id}")
async def delete_user(user_id: str):
    # Validate user_id
    if not is_valid_object_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Delete user
    result = conn.user.mortgage_details.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User with ID {user_id} has been deleted successfully"}

