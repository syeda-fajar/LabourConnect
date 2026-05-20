from fastapi import FastAPI
from sqlalchemy import text
from schedular import expire_inactive_workers
import time
import logging
from database import get_db
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Request,Depends
from fastapi.responses import JSONResponse
from routers import auth,worker,job
from datetime import datetime
from exceptions import LabourConnectException
from fastapi.exceptions import HTTPException
scheduler = BackgroundScheduler()
@asynccontextmanager
async def lifespan(app: FastAPI):
   
    scheduler.add_job(expire_inactive_workers, 'interval', hours=2,next_run_time=datetime.now())
    scheduler.start()
    print("Scheduler started...")
    
    yield
    
  
    scheduler.shutdown()
    print("Scheduler shut down.")

API_V1_STR = "/api/v1"

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router, prefix=API_V1_STR)
app.include_router(worker.router, prefix=API_V1_STR)
app.include_router(job.router, prefix=API_V1_STR)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"), 
        logging.StreamHandler()         
    ]
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def middleware_func(request:Request,call_next):
    start_time = time.time()
    method = request.method
    path=request.url.path
    client_ip = request.client.host
    response = await call_next(request) 

    process_time =(time.time() - start_time)*1000
    formatted_process_time = "{0:.2f}".format(process_time)
    logger.info(f"IP:{client_ip} | {method} {path} | Status:{response.status_code} | Time:{formatted_process_time}ms")

    return response


@app.exception_handler(LabourConnectException)
async def labour_connect_exception_handler(request: Request, exc: LabourConnectException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code
        },
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": "GenericError",
            "message": exc.detail,
            "status_code": exc.status_code
        },
    )

@app.get("/")
async def root():
    return {"message": " docker World"}

@app.get("/health")
async def HealthCheck(db:Session=Depends(get_db)):
    try:
     db.execute(text("SELECT 1"))
     return {"status": "healthy", "database": "connected"}
    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Database connection unsuccessful"
        )
