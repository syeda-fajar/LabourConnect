from database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column,Integer,String,Text,ForeignKey,Boolean,DateTime,FLOAT,UniqueConstraint,Index
class Users(Base):
    __tablename__ = "Users"
    id = Column(Integer,primary_key=True)
    name=Column(String,nullable=False)
    email =Column(String,unique=True,index=True,nullable=False)
    password=Column(String,nullable=False)
    role = Column(String, default="customer")
    worker = relationship("Worker_profile",back_populates="user")
    is_active=Column(Boolean,nullable=False,default=True)
class Worker_profile(Base):
    __tablename__ = "Workers"
    id=Column(Integer,primary_key=True)
    user_id = Column(Integer,ForeignKey("Users.id",ondelete="CASCADE"),index=True)
    phone_no = Column(String,nullable=False)
    location = Column(String,nullable=False)
    is_available = Column(Boolean, default=True)
    last_available_at = Column(DateTime, nullable=True)
    skills = relationship("Skills", secondary="Worker_skills", back_populates="workers")
    user = relationship("Users",back_populates="worker")
    average_rating = Column(FLOAT,default=0.0)
    total_rating = Column(Integer,default=0)
    hourly_rate = Column(Integer,nullable=True)

class Skills(Base):
    __tablename__ = "Skills"
    id=Column(Integer,primary_key=True)
    skills_name =Column(String,nullable=False)
    workers = relationship("Worker_profile", secondary="Worker_skills", back_populates="skills")
    __table_args__ = (
        Index(
            "ix_skills_name_trgm",      
            "skills_name",               
            postgresql_using="gin",      
            postgresql_ops={             
                "skills_name": "gin_trgm_ops"
            }
        ),
    )

class Worker_skills(Base):
    __tablename__ = "Worker_skills"
    worker_id = Column(Integer,ForeignKey("Workers.id",ondelete="CASCADE"),primary_key=True)
    skills_id = Column(Integer,ForeignKey("Skills.id",ondelete="CASCADE"),primary_key=True)

class job(Base):
    __tablename__ = "Job"
    id=Column(Integer,primary_key=True)
    customer_id =  Column(Integer,ForeignKey("Users.id",ondelete="CASCADE"),index=True)
    worker_id = Column(Integer,ForeignKey("Workers.id",ondelete="CASCADE"))
    skills_id = Column(Integer,ForeignKey("Skills.id",ondelete="CASCADE"))
    create_at=Column(DateTime,default=datetime.now)
    status = Column(String,default="pending")
    is_deleted=Column(Boolean,nullable=False,default=False)
    agreed_price = Column(Integer, nullable=False)
    __table_args__ = (
        Index(
            "idx_one_active_job_per_worker",
            "worker_id",
            unique=True,
            postgresql_where=((status.in_(["accepted", "in_progress"])) & (is_deleted == False))
        ),
    )

class Rating(Base):
    __tablename__ = "Rating"
    id = Column(Integer,primary_key=True)
    customer_id =  Column(Integer,ForeignKey("Users.id",ondelete="CASCADE"),index=True)
    worker_id = Column(Integer,ForeignKey("Workers.id",ondelete="CASCADE"))
    job_id= Column(Integer,ForeignKey("Job.id",ondelete="CASCADE"))
    score = Column(FLOAT,nullable=False)
    comment = Column(String,nullable=True)

    __table_args__ = (
        UniqueConstraint('customer_id', 'job_id', name='_customer_job_rating_uc'),
    )
