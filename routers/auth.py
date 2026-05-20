from database import engine,get_db
from models import Users,Worker_profile,Skills
from fastapi import Depends,APIRouter,status,HTTPException
from sqlalchemy.orm import Session
from schemas import UserCreate,UserOut,WorkerProfileCreate,workerUpadte
from utils import hash_password,verify_password,jwt_token
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from oauth import get_worker_role
from datetime  import datetime
from exceptions import LabourConnectException
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

    
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def RegisterUser(user: UserCreate, db: Session = Depends(get_db)):
   
    email_exists = db.query(Users).filter(Users.email == user.email).first()
    if email_exists:
        raise LabourConnectException(
            status_code=400,
            message="An account with this email address already exists.",
            error_code="EmailAlreadyRegistered"
        )
    
    hashed_pwd = hash_password(user.password)
    new_user = Users(
        email=user.email, 
        password=hashed_pwd, 
        role=user.role, 
        name=user.name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
async def login(
    user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    user = db.query(Users).filter(
        Users.email == user_credentials.username
    ).first()

    if not user or not verify_password(user_credentials.password, user.password):
        raise LabourConnectException(
            status_code=401,
            message="The email or password provided is incorrect.",
            error_code="InvalidCredentials"
        )
   
    if not user.is_active:
        raise LabourConnectException(
            status_code=403,
            message="Your account has been deactivated. Please contact support.",
            error_code="AccountDeactivated"
        )

   
    access_token = jwt_token(data={"user_id": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}