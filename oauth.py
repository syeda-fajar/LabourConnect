from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlalchemy.orm import Session
from database import get_db
from models import Users
from utils import verify_access_token
OAuth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: Annotated[str, Depends(OAuth2)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials"
    )
    user_id, role = verify_access_token(token, credentials_exception)
    user = db.query(Users).filter(Users.id == user_id).first()

    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User account is deactivated"
        )
  
    
    
    return {"id": user_id, "role": role}

def get_worker_role(current_user:Annotated[dict,Depends(get_current_user)]):
    if current_user["role"] != "worker":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Access denied. This action requires a Worker account.")
    return current_user

def get_customer_role(current_user:Annotated[dict,Depends(get_current_user)]):
    if current_user["role"] != "customer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Access denied. This action requires a Worker account.")
    return current_user