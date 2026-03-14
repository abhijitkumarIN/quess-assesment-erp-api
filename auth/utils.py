from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import random
import string
from fastapi import Depends , Request
from database.database import get_db
from constants import AUTHORIZATION
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
     return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def generate_otp(length: int = 6) -> str: 
    return ''.join(random.choices(string.digits, k=length))

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from database.config import settings
from .models import User

async def get_current_user(token: str, db: Session):
    try:
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
async def get_bearer_user(request:Request , db:Session=Depends(get_db)):
    token:str|None = request.headers.get(AUTHORIZATION)
    user =  await get_current_user(token.split()[0] ,db)
    return user 
