import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "postgresql://your_db_user:your_db_password@db:5432/your_test_db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def setup_database():
  
    Base.metadata.create_all(bind=engine)
    yield
  
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    
    def _get_test_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = _get_test_db
    
    with TestClient(app) as test_client:
        yield test_client
        
   
    app.dependency_overrides.clear()
def test_api_health_check(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_user_registration_success(client):
    unique_suffix = uuid.uuid4().hex[:6]
    unique_email = f"test_user_{unique_suffix}@example.com"
   
    payload = {
  "name": "Testuser",
  "email": unique_email,
  "password": "pass",
  "role": "customer"
}
    
   
    response = client.post("/api/v1/auth/register", json=payload)
    
   
    assert response.status_code == 201


def test_user_login_success(client):
   
    unique_suffix = uuid.uuid4().hex[:6]
    unique_email = f"login_user_{unique_suffix}@example.com"
    password_string = "MySecurePassword123"
    
    reg_payload = {
        "name": "Login Tester",
        "email": unique_email,
        "password": password_string,
        "role": "customer"
    }
   
    reg_response = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_response.status_code == 201

    login_payload = {
        "username": unique_email,  
        "password": password_string
    }
    response = client.post("/api/v1/auth/login", data=login_payload)
    

    assert response.status_code == 200
    
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_create_worker_profile_success(client):
    unique_suffix = uuid.uuid4().hex[:6]
    unique_email = f"worker_{unique_suffix}@example.com"
    password = "SecurePassword123"
    
    reg_payload = {
        "name": "Worker Handyman",
        "email": unique_email,
        "password": password,
        "role": "worker"
    }
    client.post("/api/v1/auth/register", json=reg_payload)
  
    login_payload = {"username": unique_email, "password": password}
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    token = login_response.json()["access_token"]
    
  
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
   
    worker_payload = {
        "phone_no": "+923001234567",
        "location": "Islamabad",
        "skill_ids": [], 
        "hourly_rate": 15
    }
    
  
    response = client.post("/api/v1/workers/", json=worker_payload, headers=headers)
    
  
    assert response.status_code == 201



def test_update_worker_profile_success(client):
   
    unique_suffix = uuid.uuid4().hex[:6]
    unique_email = f"patch_worker_{unique_suffix}@example.com"
    password = "SecurePassword123"
    
    reg_payload = {
        "name": "Patch Tester",
        "email": unique_email,
        "password": password,
        "role": "worker"
    }
    client.post("/api/v1/auth/register", json=reg_payload)
    
   
    login_payload = {"username": unique_email, "password": password}
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    
    initial_payload = {
        "phone_no": "+923009999999",
        "location": "Lahore",
        "skill_ids": [],
        "hourly_rate": 10
    }
    client.post("/api/v1/workers/", json=initial_payload, headers=headers)
    
    
    update_payload = {
        "is_available": False,   
        "hourly_rate": 45        
    }
    
    response = client.patch("/api/v1/workers/", json=update_payload, headers=headers)
    
  
    assert response.status_code == 200
    
    response_data = response.json()
    assert response_data["is_available"] is False
    assert response_data["hourly_rate"] == 45



def test_job_booking_success(client):
   #worker
    worker_suffix = uuid.uuid4().hex[:6]
    worker_email = f"target_worker_{worker_suffix}@example.com"
    password = "SecurePassword123"
    
    client.post("/api/v1/auth/register", json={
        "name": "Available Worker",
        "email": worker_email,
        "password": password,
        "role": "worker"
    })
    
    w_login = client.post("/api/v1/auth/login", data={"username": worker_email, "password": password})
    worker_token = w_login.json()["access_token"]
    
    profile_payload = {
        "phone_no": "+923001112223", 
        "location": "G-11 Islamabad", 
        "skill_ids": [1], 
        "hourly_rate": 30
    }
    
    profile_response = client.post(
        "/api/v1/workers/", 
        json=profile_payload, 
        headers={"Authorization": f"Bearer {worker_token}"}
    )
    assert profile_response.status_code == 201
    real_worker_id = profile_response.json()["id"]
    
   #customer
    customer_suffix = uuid.uuid4().hex[:6]
    customer_email = f"hiring_customer_{customer_suffix}@example.com"
    
    client.post("/api/v1/auth/register", json={
        "name": "Employer Customer",
        "email": customer_email,
        "password": password,
        "role": "customer"
    })
    
    c_login = client.post("/api/v1/auth/login", data={"username": customer_email, "password": password})
    customer_token = c_login.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    
    job_payload = {
        "worker_id": real_worker_id,
        "skills_id": 1 
    }
    
    response = client.post("/api/v1/jobs/", json=job_payload, headers=customer_headers)
    
    assert response.status_code == 201

def test_job_status_update_success(client):
    #  Worker & Customer
    worker_suffix = uuid.uuid4().hex[:6]
    worker_email = f"status_w_{worker_suffix}@example.com"
    password = "SecurePassword123"
    
    client.post("/api/v1/auth/register", json={"name": "S Worker", "email": worker_email, "password": password, "role": "worker"})
    w_login = client.post("/api/v1/auth/login", data={"username": worker_email, "password": password})
    worker_token = w_login.json()["access_token"]
    worker_headers = {"Authorization": f"Bearer {worker_token}"}
    
    profile_res = client.post("/api/v1/workers/", json={"phone_no": "+923007777777", "location": "Islamabad", "skill_ids": [1], "hourly_rate": 25}, headers=worker_headers)
    real_worker_id = profile_res.json()["id"]
    
    customer_suffix = uuid.uuid4().hex[:6]
    customer_email = f"status_c_{customer_suffix}@example.com"
    client.post("/api/v1/auth/register", json={"name": "S Customer", "email": customer_email, "password": password, "role": "customer"})
    c_login = client.post("/api/v1/auth/login", data={"username": customer_email, "password": password})
    customer_token = c_login.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    
    # Book Job 
    booking_res = client.post("/api/v1/jobs/", json={"worker_id": real_worker_id, "skills_id": 1}, headers=customer_headers)
    job_id = booking_res.json()["id"]
    
    #  Transition pending -> accepted
    res1 = client.patch(f"/api/v1/jobs/{job_id}/status", json={"status": "accepted"}, headers=worker_headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "accepted"

    #  accepted -> in_progress
    res2 = client.patch(f"/api/v1/jobs/{job_id}/status", json={"status": "in_progress"}, headers=worker_headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "in_progress"


def test_create_job_rating_success(client):
    #  Worker & Customer
    worker_suffix = uuid.uuid4().hex[:6]
    worker_email = f"rate_w_{worker_suffix}@example.com"
    password = "SecurePassword123"
    
    client.post("/api/v1/auth/register", json={"name": "R Worker", "email": worker_email, "password": password, "role": "worker"})
    w_login = client.post("/api/v1/auth/login", data={"username": worker_email, "password": password})
    worker_token = w_login.json()["access_token"]
    worker_headers = {"Authorization": f"Bearer {worker_token}"}
    
    profile_res = client.post("/api/v1/workers/", json={"phone_no": "+923004444444", "location": "Peshawar", "skill_ids": [1], "hourly_rate": 20}, headers=worker_headers)
    real_worker_id = profile_res.json()["id"]
    
    customer_suffix = uuid.uuid4().hex[:6]
    customer_email = f"rate_c_{customer_suffix}@example.com"
    client.post("/api/v1/auth/register", json={"name": "R Customer", "email": customer_email, "password": password, "role": "customer"})
    c_login = client.post("/api/v1/auth/login", data={"username": customer_email, "password": password})
    customer_token = c_login.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    
    # Book Job
    booking_res = client.post("/api/v1/jobs/", json={"worker_id": real_worker_id, "skills_id": 1}, headers=customer_headers)
    job_id = booking_res.json()["id"]

  
   
    client.patch(f"/api/v1/jobs/{job_id}/status", json={"status": "accepted"}, headers=worker_headers)

    client.patch(f"/api/v1/jobs/{job_id}/status", json={"status": "in_progress"}, headers=worker_headers)
    
    completion_res = client.patch(f"/api/v1/jobs/{job_id}/status", json={"status": "completed"}, headers=customer_headers)
    assert completion_res.status_code == 200

    # Submit Rating
    rating_payload = {"score": 5, "comment": "Excellent work!"}
    response = client.post(f"/api/v1/jobs/rating/{job_id}", json=rating_payload, headers=customer_headers)
    
    assert response.status_code == 201

def test_job_deletion_and_safety_rules(client):
    
    customer_suffix = uuid.uuid4().hex[:6]
    customer_email = f"delete_c_{customer_suffix}@example.com"
    password = "SecurePassword123"
    client.post("/api/v1/auth/register", json={"name": "D Customer", "email": customer_email, "password": password, "role": "customer"})
    c_login = client.post("/api/v1/auth/login", data={"username": customer_email, "password": password})
    customer_token = c_login.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

  
    w1_suffix = uuid.uuid4().hex[:6]
    w1_email = f"delete_w1_{w1_suffix}@example.com"
    client.post("/api/v1/auth/register", json={"name": "D Worker 1", "email": w1_email, "password": password, "role": "worker"})
    w1_login = client.post("/api/v1/auth/login", data={"username": w1_email, "password": password})
    w1_token = w1_login.json()["access_token"]
    w1_profile = client.post("/api/v1/workers/", json={"phone_no": "+923008888881", "location": "Rawalpindi", "skill_ids": [1], "hourly_rate": 20}, headers={"Authorization": f"Bearer {w1_token}"})
    worker1_id = w1_profile.json()["id"]

 
    w2_suffix = uuid.uuid4().hex[:6]
    w2_email = f"delete_w2_{w2_suffix}@example.com"
    client.post("/api/v1/auth/register", json={"name": "D Worker 2", "email": w2_email, "password": password, "role": "worker"})
    w2_login = client.post("/api/v1/auth/login", data={"username": w2_email, "password": password})
    w2_token = w2_login.json()["access_token"]
    w2_profile = client.post("/api/v1/workers/", json={"phone_no": "+923008888882", "location": "Rawalpindi", "skill_ids": [1], "hourly_rate": 20}, headers={"Authorization": f"Bearer {w2_token}"})
    worker2_id = w2_profile.json()["id"]
    
   
    booking_res1 = client.post("/api/v1/jobs/", json={"worker_id": worker1_id, "skills_id": 1}, headers=customer_headers)
    assert booking_res1.status_code == 201
    job_id_pending = booking_res1.json()["id"]
    

    booking_res2 = client.post("/api/v1/jobs/", json={"worker_id": worker2_id, "skills_id": 1}, headers=customer_headers)
    if booking_res2.status_code != 201:
        print("\n--- BOOKING 2 ERROR DEBUG ---")
        print(booking_res2.json())
    assert booking_res2.status_code == 201
    job_id_accepted = booking_res2.json()["id"]
    
   
    client.patch(f"/api/v1/jobs/{job_id_accepted}/status", json={"status": "accepted"}, headers={"Authorization": f"Bearer {w2_token}"})

  
    worker_del_res = client.delete(f"/api/v1/jobs/{job_id_pending}", headers={"Authorization": f"Bearer {w1_token}"})
    assert worker_del_res.status_code == 403
    assert worker_del_res.json()["error_code"] == "ActionForbidden"

   
    customer_bad_del = client.delete(f"/api/v1/jobs/{job_id_accepted}", headers=customer_headers)
    assert customer_bad_del.status_code == 400
    assert customer_bad_del.json()["error_code"] == "InvalidAction"

 
    customer_good_del = client.delete(f"/api/v1/jobs/{job_id_pending}", headers=customer_headers)
    assert customer_good_del.status_code == 200