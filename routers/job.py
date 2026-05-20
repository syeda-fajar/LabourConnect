from database import engine,get_db
from models import Users,Worker_profile,Worker_skills,job,Rating
from fastapi import Depends,APIRouter,status,HTTPException
from schemas import CreateBooking,statusUpdate,RatingScore
from oauth import get_worker_role,get_customer_role,get_current_user
from sqlalchemy.orm import Session
from exceptions import LabourConnectException
from sqlalchemy.exc import IntegrityError
import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/",status_code=status.HTTP_201_CREATED)
async def JobBooking(
    worker_Data:CreateBooking,
    db: Session = Depends(get_db),
    currentUser: dict = Depends(get_customer_role),
    ):
    worker_exist = db.query(Worker_profile).filter(Worker_profile.id==worker_Data.worker_id).first()
    if not worker_exist:
        raise LabourConnectException(
            status_code=404,
            message="The requested worker profile does not exist.",
            error_code="WorkerNotFound"
        )
    
    if (worker_exist.is_available==False):
        raise LabourConnectException(
            status_code=400,
            message="This worker is currently busy with another job.",
            error_code="WorkerUnavailable"
        )
    

    skills_exist= db.query(Worker_skills).filter(Worker_skills.worker_id==worker_Data.worker_id,Worker_skills.skills_id==worker_Data.skills_id).first()
    if not skills_exist:
         raise LabourConnectException(
            status_code=400,
            message="This worker does not provide the specific skill requested.",
            error_code="SkillMismatch"
        )
    
    active_job = db.query(job).filter(
        job.customer_id == currentUser["id"],
        job.worker_id == worker_Data.worker_id,
        job.status.in_(["pending", "accepted", "in_progress"]),
        job.is_deleted == False
    ).first()
    if active_job:
        raise LabourConnectException(
            status_code=400,
            message=f"You already have an active booking with this worker. Current status: {active_job.status}",
            error_code="DuplicateBooking"
        )
    
    if worker_exist.hourly_rate is None or worker_exist.hourly_rate <= 0:
        raise LabourConnectException(
            status_code=400,
            message="This worker has not set a valid hourly rate yet. Booking cannot proceed.",
            error_code="RateNotSet"
        )

    new_job =job(customer_id=currentUser["id"],
                 worker_id=worker_Data.worker_id,
                 skills_id =worker_Data.skills_id,
                 agreed_price=worker_exist.hourly_rate
                 )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job




@router.patch("/{job_id}/status", status_code=status.HTTP_200_OK)
async def JobStatus(
    job_id: int,
    status_update: statusUpdate,
    db: Session = Depends(get_db),
    currentUser: dict = Depends(get_current_user),
):
    job_exist = db.query(job).filter(job.id == job_id).first()

    if not job_exist:
        raise LabourConnectException(
            status_code=404,
            message="The requested job record was not found.",
            error_code="JobNotFound"
        )
    
    if job_exist.is_deleted: 
        raise LabourConnectException(
            status_code=400,
            message="This job has been cancelled and cannot be modified.",
            error_code="JobCancelled"
        )

    current = job_exist.status.lower()
    requested = status_update.status.lower()

    if currentUser["role"] == "worker":
        worker_profile = db.query(Worker_profile).filter(Worker_profile.user_id == currentUser["id"]).first()
        
        if not worker_profile:
             raise LabourConnectException(
                status_code=403,
                message="You must create a worker profile before managing jobs.",
                error_code="ProfileMissing"
            )

        if job_exist.worker_id != worker_profile.id:
            raise LabourConnectException(
                status_code=403,
                message="You are not authorized to manage this specific job.",
                error_code="AccessDenied"
            )

        is_valid_transition = (current == "pending" and requested in ["accepted", "rejected"]) or \
                              (current == "accepted" and requested == "in_progress")
        
        if is_valid_transition:
            result = db.query(job).filter(job.id == job_id, job.status == current).update({"status": requested})
            job_exist.status = requested
            
            if result == 0:
                 raise LabourConnectException(
                    status_code=409, 
                    message="Job status was modified by another user. Refresh and try again.",
                    error_code="RaceCondition"
                )
            
            if requested in ["accepted", "in_progress"]:
                worker_profile.is_available = False
                logger.info(f"Worker {worker_profile.id} is now BUSY.")
            elif requested == "rejected":
                worker_profile.is_available = True
        else:
             raise LabourConnectException(
                status_code=400,
                message=f"Invalid move: Cannot change status from {current} to {requested}.",
                error_code="InvalidTransition"
            )

    elif currentUser["role"] == "customer":
        if job_exist.customer_id != currentUser["id"]:
            raise LabourConnectException(
                status_code=403,
                message="You do not own this booking.",
                error_code="AccessDenied"
            )
        
        if current == "in_progress" and requested == "completed":
            result = db.query(job).filter(job.id == job_id, job.status == "in_progress").update({"status": "completed"})
            
            if result == 0:
                raise LabourConnectException(
                    status_code=409,
                    message="The job status has already changed.",
                    error_code="RaceCondition"
                )

            worker_to_release = db.query(Worker_profile).filter(Worker_profile.id == job_exist.worker_id).first()
            if worker_to_release:
                worker_to_release.is_available = True
        else:
            raise LabourConnectException(
                status_code=400,
                message="Only jobs 'in_progress' can be marked as 'completed'.",
                error_code="InvalidTransition"
            )
    
    db.commit()
    db.refresh(job_exist)
    return job_exist


@router.post("/rating/{job_id}", status_code=status.HTTP_201_CREATED)
async def CreateRating(
    job_id: int,
    rating: RatingScore,
    currentUser: dict = Depends(get_customer_role),
    db: Session = Depends(get_db)
):
    job_exist = db.query(job).filter(job.id == job_id).first()

    if not job_exist:
        raise LabourConnectException(404, "Job not found.", "JobNotFound")
    
    if not job_exist.customer_id == currentUser["id"]:
        raise LabourConnectException(403, "You can only rate jobs you booked.", "AccessDenied")
    
    if not job_exist.status == "completed":
        raise LabourConnectException(400, "You can only rate completed jobs.", "InvalidAction")
    
    worker_to_rate = db.query(Worker_profile).filter(Worker_profile.id == job_exist.worker_id).first()

    if not worker_to_rate:
        raise LabourConnectException(404, "Worker profile no longer exists.", "ProfileNotFound")

    if worker_to_rate.user_id == currentUser['id']:
        raise LabourConnectException(403, "Self-rating is strictly prohibited.", "SelfRatingForbidden")

    new_rating = Rating(
        customer_id=currentUser["id"],
        worker_id=job_exist.worker_id,
        job_id=job_exist.id,
        score=rating.score
    )

    try:
        db.add(new_rating)
        
     
        if not worker_to_rate.total_rating:
            worker_to_rate.average_rating = rating.score
            worker_to_rate.total_rating = 1
        else:
            old_count = worker_to_rate.total_rating
            new_count = old_count + 1
            new_avg = ((worker_to_rate.average_rating * old_count) + rating.score) / new_count
            worker_to_rate.average_rating = round(new_avg, 2)
            worker_to_rate.total_rating = new_count
        
        db.commit()
        
    except IntegrityError:
        db.rollback() 
        raise LabourConnectException(400, "You have already rated this job.", "DuplicateRating")

    db.refresh(new_rating)
    return {"message": "Rating submitted successfully", "new_average": worker_to_rate.average_rating}


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    currentUser: dict = Depends(get_current_user)
):
    job_exist = db.query(job).filter(job.id == job_id).first()

    if not job_exist:
        raise LabourConnectException(404, "Job not found.", "JobNotFound")
    
    if currentUser["role"] == "customer":
        if not job_exist.customer_id == currentUser["id"]:
            raise LabourConnectException(403, "Access denied.", "AccessDenied")
        if not job_exist.status == "pending":
            raise LabourConnectException(400, "Only pending jobs can be cancelled.", "InvalidAction")
        
        job_exist.is_deleted = True
        db.commit() 
        return {"message": "Job request cancelled successfully"}
    
    if currentUser["role"] == "worker":
        raise LabourConnectException(403, "Workers must 'reject' jobs, not delete them.", "ActionForbidden")
    

@router.get("/top-rated")
async def get_top_workers(db: Session = Depends(get_db)):
    top_workers = db.query(Worker_profile).filter(
        Worker_profile.total_rating > 0
    ).order_by(Worker_profile.average_rating.desc()).limit(10).all()
    
    return top_workers

@router.get("/worker/{worker_id}/reviews")
async def get_worker_reviews(worker_id: int, db: Session = Depends(get_db)):
    
   reviews = db.query(Rating).join(job).filter(
      Rating.worker_id == worker_id,
      job.is_deleted == False
       ).all()
   return reviews
