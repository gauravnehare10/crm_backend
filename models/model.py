from pydantic import BaseModel
from typing import Optional, Dict

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

class UserUpdate(BaseModel):
    username: str
    name: str
    email: str
    contactnumber: int
    bankname: str | None = None
    branch: str | None = None
    acctype: str | None = None
    dob: str | None = None
    address: str | None = None


class MortgageDetails(BaseModel):
    hasMortgage: bool
    username: str
    mortgageCount: Optional[int] = None
    mortgageType: Optional[str] = None
    mortgageAmount: Optional[str] = None
    renewalDate: Optional[str] = None
    isLookingForMortgage: Optional[bool] = None
    newMortgageAmount: Optional[str] = None
    ownershipType: Optional[str] = None
    annualIncome: Optional[str] = None

