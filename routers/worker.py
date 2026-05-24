from database import engine,get_db
from models import Users,Worker_profile,Skills
from fastapi import Depends,APIRouter,status,HTTPException
from sqlalchemy.orm import Session,join,joinedload
from schemas import WorkerProfileCreate,workerUpadte,PaginatedWorkerResponse,WorkerSearchOut
from typing import Optional,List
from oauth import get_worker_role
from datetime  import datetime
import json
from fastapi.encoders import jsonable_encoder
from redis_config import redis_client
import logging
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/workers",
    tags=["Workers"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def workerProfileCreate(
    worker_data: WorkerProfileCreate, 
    db: Session = Depends(get_db),
    currentUser: dict = Depends(get_worker_role)
):
   
    existing_profile = db.query(Worker_profile).filter(Worker_profile.user_id == currentUser["id"]).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Worker profile already exists.")

    new_profile = Worker_profile(
        user_id=currentUser["id"], 
        phone_no=worker_data.phone_no,
        location=worker_data.location,
        hourly_rate = worker_data.hourly_rate
    )

    if worker_data.skill_ids:
        skills_from_db = db.query(Skills).filter(Skills.id.in_(worker_data.skill_ids)).all()
        if len(skills_from_db) != len(worker_data.skill_ids):
            raise HTTPException(status_code=404, detail="One or more skill IDs not found")
        
       
        new_profile.skills = skills_from_db
        
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile





@router.get("/", response_model=PaginatedWorkerResponse)
async def get_workers(
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 5,
    location: Optional[str] = None,
    skill: Optional[str] = None,
    available_only: bool = False
):
    skill_key = skill.strip().lower() if skill else "all"
    location_key = location.strip().lower() if location else "all"
    cache_key = f"search:{skill_key}:{location_key}:{page}:{size}:{available_only}"

  
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"CACHE HIT: Returning results for key {cache_key}")
                return json.loads(cached_result)
        except Exception as e:
            logger.error(f"Redis lookup failed, falling back to database: {e}")

    logger.info(f"CACHE MISS: Fetching from PostgreSQL for key {cache_key}")

   
    query = db.query(Worker_profile).options(joinedload(Worker_profile.user))
    
    if skill:
        query = query.join(Worker_profile.skills).filter(Skills.skills_name.ilike(f"%{skill}%"))
    
    if location:
        query = query.filter(Worker_profile.location.ilike(f"%{location}%"))
    
    if available_only:
        query = query.filter(Worker_profile.is_available == True)

    query = query.join(Users).filter(Users.is_active == True)
    total = query.count()
    
    skip = (page - 1) * size
    workers = query.offset(skip).limit(size).all()
    
    raw_response = {
        "total": total,
        "page": page,
        "size": size,
        "data": workers
    }

    
    serializable_response = jsonable_encoder(raw_response)

  
    if redis_client:
        try:
            redis_client.setex(cache_key, 300, json.dumps(serializable_response))
            logger.info(f"CACHE POPULATED: Key {cache_key} stored for 5 minutes.")
        except Exception as e:
            logger.error(f"Failed to save data to Redis: {e}")

    return serializable_response