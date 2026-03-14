from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime , timedelta
from database.database import get_db
from .schemas import UserOut, UserCreate , UserLogin , Token
from .models import User
from .utils import get_password_hash , generate_otp , create_access_token , get_current_user
from utils.main import send_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user.password)
    otp = generate_otp()
    logger.debug("signup payload: %s", getattr(user, "__dict__", str(user)))
    try:
        send_email(
            email=user.email,
            subject="OTP Verification",
            body=f"Your OTP code is {otp}. Please use this code to verify your email."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {str(e)}"
        )
    # defensive construction: don't pass potentially-invalid kwargs to the model constructor
    try:
        new_user = User()
    except TypeError:
        # some models may require at least an email in constructor; try that as a fallback
        try:
            new_user = User(email=user.email)
        except TypeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to construct User model instance; check model constructor"
            )

    # assign attributes safely (skip any that the model doesn't accept)
    attrs = {
        "email": user.email,
        "username": getattr(user, "username", None),
        "hashed_password": hashed_password,
        "otp": otp,
        "otp_created_at": datetime.utcnow(),
        # ensure response-required field is present
        "is_active": False,
    }
    for name, val in attrs.items():
        if val is None:
            continue
        try:
            setattr(new_user, name, val)
        except Exception:
            logger.debug("Could not set %s on User instance; skipping", name)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@router.post('/verify-account')
async def verify_account(email:str , otp:str , db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user :
        raise HTTPException(
            status_code=404 , detail="User not found"
        )
    if user.otp != otp:
        raise HTTPException(
            status_code=400 , detail="Invalid OTP"
        )
    if datetime.utcnow>= user.otp_created_at + timedelta(minutes=15):
        raise HTTPException(
            status_code=400 , detail="OTP expired"
        )
    user.is_verified =True 
    user.otp=None
    user.is_active=True
    user.otp_created_at=None
    db.commit()
    return {
        "message":"Email verified successfully"
    }

@router.post("/login" , response_model=Token)
async def login(user_credential:UserLogin , db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email ==  user_credential.email).first()
    if not user :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credential"
        )
    if  user.is_verified :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not verified"
        )
    access_token = create_access_token(data={
        "sub":user.email
    })
    hold_customer = await get_current_user(
        access_token , db
    )
    logger.debug(hold_customer)
    return {
        "access_token":access_token , "token_type":"bearer"
    }

@router.post('/forgot-password' , response_model=str)
async def forgot_password(email:str , db: Session=Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user :
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED ,
            detail="Provided mail does exist"
        )
    access_token = create_access_token(data={"sub":email})
    await send_email(
        email=email,
        subject="Forgot password link",
        body=f"your grand access link valid for 2 hours {access_token}"
    ) 
    return "Grand access token has been shared with your account mail id it is valid for 2 hours"




@router.post('/change-password')
async def change_password(password: str, request: Request, db: Session = Depends(get_db)):
    try:
        user_data = request.state.user
        user_id = getattr(user_data, 'id', None) or user_data.get('sub')
        current_user = db.query(User).filter((User.email == user_id) | (User.id == user_id)).first()
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        hashed_password = get_password_hash(password)
        current_user.hashed_password = hashed_password
        db.commit()
        email = current_user.email
        if email:
            send_email(
                email=email,
                subject="Blog Test API | Password has been fixed",
                body="Password has been updated successfully"
            )
        return {
            "message": "Password has been updated successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
