import os
import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ArgumentError, OperationalError
from dotenv import load_dotenv

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
def get_engine_with_retry(url, max_retries=5, delay=2):
   
    if not url:
        print("Error: DATABASE_URL is None. Cannot create engine.")
        return None

    attempt = 0
    while attempt < max_retries:
        try:
            print(f"Attempting to connect to DB (Attempt {attempt + 1}/{max_retries})...")
            engine = create_engine(url)
            
            with engine.connect() as conn:
                pass
            print("Database connection successful!")
            return engine
        except (OperationalError, ArgumentError) as e:
            attempt += 1
            print(f"Connection failed: {e}")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                raise e

engine = get_engine_with_retry(SQLALCHEMY_DATABASE_URL)


if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

Base = declarative_base()

def get_db():
    if SessionLocal is None:
        raise Exception("Database session could not be initialized. Check DATABASE_URL.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()