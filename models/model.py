from pydantic import BaseModel
from typing import Optional, Dict, List

class User(BaseModel):
    name: str
    username: str
    email: str
    contactnumber: int
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_details: Optional[Dict[str, str]]
    mortgage: Optional[Dict[str, str]]

class AdminToken(BaseModel):
    access_token: str
    token_type: str
    admin_details: Optional[Dict[str, str]]


class MortgageDetails(BaseModel):
    username: str
    hasMortgage: bool
    mortgageCount: Optional[str] = None
    resOrBuyToLet: Optional[str] = None
    mortgageType: Optional[str] = None
    mortgageAmount: Optional[str] = None
    mortgageAmount2: Optional[str] = None
    mortgageAmount3: Optional[str] = None
    renewalDate: Optional[str] = None
    isLookingForMortgage: Optional[bool] = None
    newMortgageAmount: Optional[str] = None
    ownershipType: Optional[str] = None
    depositeAmt: Optional[str] = None
    annualIncome: Optional[str] = None
    foundProperty: Optional[str] = None



class ExistingMortgageDetails(BaseModel):
    id: str
    hasMortgage: bool
    mortgageCount: Optional[str] = None
    mortgageType: Optional[str] = None
    renewalDate: Optional[str] = None
    mortgageAmount: Optional[str] = None
    mortgageAmount2: Optional[str] = None
    mortgageAmount3: Optional[str] = None
    resOrBuyToLet: Optional[str] = None


class NewMortgageRequest(BaseModel):
    id: str
    isLookingForMortgage: bool
    newMortgageAmount: Optional[str] = None
    ownershipType: Optional[str] = None
    annualIncome: Optional[str] = None
    depositeAmt: Optional[str] = None
    foundProperty: Optional[str] = None

class UserUpdate(BaseModel):
    name: str
    username: str
    email: str
    contactnumber: int

class AllUser(BaseModel):
    id: str  # Serialized `_id` from MongoDB
    name: str
    username: str
    email: str
    contactnumber: int
    mortgage_details: Optional[List[ExistingMortgageDetails]] = []
    new_mortgage_requests: Optional[List[NewMortgageRequest]] = []


class PasswordResetRequest(BaseModel):
    email: str

class PasswordChangeRequest(BaseModel):
    token: str
    new_password: str
    