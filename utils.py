from passlib.context import CryptContext
from jose import jwt,JWTError
from dotenv import load_dotenv
import os
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


ALGORITHM="HS256"


def hash_password(password:str):
    return pwd_context.hash(password)
def verify_password(plain_password:str,hashed_password:str):
    return pwd_context.verify(plain_password,hashed_password)

def jwt_token(data:dict):
    encoded_jwt=jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")
        
        if user_id is None:
            raise credentials_exception
        if role is None:
            raise credentials_exception
        
        return user_id ,role
        
    except JWTError:
        raise credentials_exception