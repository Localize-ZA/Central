import os
import binascii
import hashlib
import uuid as _uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from Data.models import Citizen, Business, Manufacturer, get_db
from Data.dto import CitizenRegistration, Login, BusinessRegister

router = APIRouter()

# --- Password hashing helpers (PBKDF2-HMAC, dependency-free) ---
def _hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return {
        "salt": binascii.hexlify(salt).decode("ascii"),
        "hash": binascii.hexlify(dk).decode("ascii"),
    }

def _verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    try:
        salt = binascii.unhexlify(salt_hex.encode("ascii"))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return binascii.hexlify(dk).decode("ascii") == hash_hex
    except Exception:
        return False

@router.post("/login/Citizen")
async def LoginCitizen(login: Login, db: Session = Depends(get_db)):
    # Lookup by email
    citizen = db.query(Citizen).filter(Citizen.email == login.email).first()
    if not citizen:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not _verify_password(login.password, citizen.salt, citizen.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {
        "citizen_id": citizen.citizen_id,
        "uuid": citizen.uuid,
        "email": citizen.email,
        "name": citizen.name,
        "surname": citizen.surname,
    }

@router.post("/login/Business")
async def LoginBusiness(login: Login, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.email == login.email).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not _verify_password(login.password, business.salt, business.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {
        "business_id": business.business_id,
        "uuid": business.uuid,
        "email": business.email,
        "business_name": business.business_name,
        "business_reg_id": business.business_reg_id,
    }

@router.post("/register/citizen", status_code=status.HTTP_201_CREATED)
async def RegisterCitizen(citizen: CitizenRegistration, db: Session = Depends(get_db)):
    # Uniqueness checks: email, gov_id
    errors: Dict[str, str] = {}

    if db.query(Citizen).filter(Citizen.email == citizen.email).first():
        errors["email"] = "already taken"

    # govId may be optional in DTO; only check if provided
    gov_id_value = getattr(citizen, "govId", None)
    if gov_id_value and db.query(Citizen).filter(Citizen.gov_id == gov_id_value).first():
        errors["govId"] = "already taken"

    if errors:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=errors)

    # Create citizen
    pw = _hash_password(citizen.password)
    citizen_row = Citizen(
        uuid=str(_uuid.uuid4()),
        gov_id=gov_id_value,
        name=citizen.firstName,
        surname=citizen.lastName,
        email=citizen.email,
        password_hash=pw["hash"],
        salt=pw["salt"],
    )

    try:
        db.add(citizen_row)
        db.commit()
        db.refresh(citizen_row)
    except IntegrityError:
        db.rollback()
        # Fall back to generic conflict if race condition
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unique constraint violated")

    return {
        "citizen_id": citizen_row.citizen_id,
        "uuid": citizen_row.uuid,
        "email": citizen_row.email,
    }

@router.post("/register/business", status_code=status.HTTP_201_CREATED)
async def RegisterBusiness(business: BusinessRegister, db: Session = Depends(get_db)):
    # Uniqueness checks: email, business_reg_id
    errors: Dict[str, str] = {}

    if db.query(Business).filter(Business.email == business.email).first():
        errors["email"] = "already taken"

    if db.query(Business).filter(Business.business_reg_id == business.businessRegId).first():
        errors["businessRegId"] = "already taken"

    if errors:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=errors)

    pw = _hash_password(business.password)
    business_row = Business(
        uuid=str(_uuid.uuid4()),
        business_name=business.businessName,
        business_reg_id=business.businessRegId,
        email=business.email,
        province=business.province,
        city=business.city,
        address1=business.address1,
        longitude=getattr(business, "longitude", None),
        latitude=getattr(business, "latitude", None),
        password_hash=pw["hash"],
        salt=pw["salt"],
    )

    try:
        db.add(business_row)
        db.commit()
        db.refresh(business_row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unique constraint violated")

    return {
        "business_id": business_row.business_id,
        "uuid": business_row.uuid,
        "email": business_row.email,
        "business_reg_id": business_row.business_reg_id,
    }