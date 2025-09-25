from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, EmailStr
from typing import Optional

'''
 Base Registration DTO
 declare type SignUpParams = {
  firstName: string;
  lastName: string;
  address1: string;
  city: string;
  state: string;
  postalCode: string;
  dateOfBirth: string;
  ssn: string;
  email: string;
  password: string;
};
'''

class CitizenToBusiness(BaseModel):
    businessRegID: str
    citizenID: str
    products: dict[str, int]
    time: Optional[str] = None
    
class Login(BaseModel):
    email: EmailStr
    password: str

class CitizenRegistration(BaseModel):
    # Minimal fields aligned with Citizen model; optional extras for future use
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    govId: Optional[str] = None
    dateOfBirth: Optional[str] = None
    address1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None


class BusinessRegister(BaseModel):
    businessName: str
    businessRegId: str
    email: EmailStr
    password: str
    province: str
    city: str
    address1: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    business_type: Optional[str] = None  # New field for business type