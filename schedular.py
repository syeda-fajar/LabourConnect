from datetime import datetime, timedelta
from database import SessionLocal
from models import Worker_profile
from sqlalchemy import or_  

def expire_inactive_workers():
    print("--- JANITOR IS CHECKING FOR EXPIRED WORKERS ---")
    
    threshold = datetime.now() - timedelta(hours=2)
    
    with SessionLocal() as db:
        expired_count = db.query(Worker_profile).filter(
            Worker_profile.is_available == True,
            or_(
                Worker_profile.last_available_at <= threshold,
                Worker_profile.last_available_at == None
            )
        ).update({Worker_profile.is_available: False}, synchronize_session=False)
        
        db.commit()
        print(f"Cleanup complete. {expired_count} workers set to unavailable.")