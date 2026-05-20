
from pydantic import BaseModel,EmailStr,StrictBool,Field,ConfigDict
from typing import Optional
class UserCreate(BaseModel):
      name: str
      email: EmailStr
      password: str
      role: str = "customer"

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class WorkerProfileCreate(BaseModel):
    phone_no: str
    location: str
    skill_ids: list[int]  
    hourly_rate : Optional[int] = None

class workerUpadte(BaseModel):
     is_available:StrictBool
     hourly_rate: Optional[int] = None


class WorkerSearchOut(BaseModel):
    id: int
    user_id: Optional[int] = None 
    location: str
    phone_no: str
    is_available: bool
    average_rating: Optional[float] = 0.0
    total_rating: Optional[int] = 0       
    user: Optional[UserOut] = None   
    hourly_rate : Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedWorkerResponse(BaseModel):
    total: int
    page: int
    size: int
    data: list[WorkerSearchOut]

    model_config = ConfigDict(from_attributes=True)

class CreateBooking(BaseModel):
    worker_id: int
    skills_id: int

class statusUpdate(BaseModel):
    status: str

class RatingScore(BaseModel):
    score:float =Field(ge=1, le=5)
    comment:Optional[str] = Field(None, description="Optional user comment")



    