# LabourConnect: Local Service Marketplace Backend

LabourConnect is a FastAPI-based backend application designed to solve a common problem in local service markets: connecting customers with verified, available workers while keeping data clean, reliable, and secure.

I built this project to practice advanced backend design, focusing heavily on database integrity, secure role-based access, caching, and handling  concurrency issues like race conditions.

---

##  Key Features

- **Role-Based Authentication:** Uses secure JSON Web Tokens (JWT) to separate access between `customers` and `workers`.
- **Smart Profiles:** Keeps application logic clean by isolating user account data from specific worker details (like skills and availability).
- **Skill Mapping:** Implements a many-to-many relationship allowing workers to link multiple skills to their profiles.
- **Job Workflow Engine:** Enforces a strict state machine for bookings (`Pending` → `Accepted` → `In-Progress` → `Completed`).
- **Price Tracking Lock:** Captures and stores the agreed hourly price at the exact moment of booking, making it immune to future worker profile price updates.
- **Safe Review System:** Prevents fraudulent ratings with strict database constraints and lifecycle checks.
- **Race Condition Protection:** Uses advanced database-level row locking to prevent workers from double-booking themselves.

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.10+) |
| Database | PostgreSQL with SQLAlchemy ORM |
| Migrations | Alembic |
| Caching | Redis 7 |
| Containerization | Docker & Docker Compose |
| Validation | Pydantic |

---

##  Key Engineering Decisions & Learning Milestones

### 1. Database Schema & Role Separation

To support a multi-user marketplace, I chose a relational PostgreSQL database. I designed a shared `Users` table for authentication, which links out to a specialized `Workers` table. This keeps queries fast and ensures that a customer cannot accidentally access worker-specific routes or modify worker metrics.

### 2. Job Status State Machine

To avoid messy business logic anomalies (like a worker marking a job as "Completed" before it was even "Accepted"), I built a validation layer inside the status route. It checks the current state against a  *** need upsdt strict transition matrix ***  before allowing any updates to pass through.

### 3. Preventing Double-Bookings (The Double Safety Net)

During development, I discovered a  race condition: if a worker has multiple pending jobs on their dashboard and clicks "Accept" on two different tabs at the exact same millisecond, standard application code allows both to be accepted.

To fix this, I implemented a two-layer solution combining Application Locking and a Database Constraint to act as a double safety net.
- **Layer 1: The Code Lock** (`with_for_update()`)
Inside my status update route, I fetch the worker's profile using PostgreSQL's row-locking mechanism

```python

worker_profile = db.query(Worker_profile).filter(
    Worker_profile.user_id == currentUser["id"]
).with_for_update().first()
```
By adding `.with_for_update()`, the second concurrent request is forced to freeze at the front gate before running any Python checks. This is critical because if I only relied on a database crash at the end, the second request might trigger external side-effects (like sending automated SMS alerts) before failing. Locking the row first protects the system from accidental side-effects and lets me return a clean `400 Bad Request` instead of a server crash.
- **Layer 2: The Database  (Partial Unique Index)**
As a final line of defense, I kept the PostgreSQL partial unique index (`idx_one_active_job_per_worker`) active on the database schema. If a future code modification accidentally bypasses the .with_for_update() check, the database index will still intercept the write and reject the duplicate active assignment.

Using both methods ensures clean application handling while making data corruption physically impossible

### 4. Securing the Trust Layer (Ratings)

To stop users from gaming the rating system, I engineered multiple defensive checks:

- **No Ghost Reviews:** Ratings are locked out until the job status explicitly reaches `Completed`.
- **No Self-Promotion:** The system cross-references IDs to ensure a worker cannot create an alternate customer account to rate themselves.
- **One Review per Job:** A PostgreSQL `UniqueConstraint` on the `customer_id` and `job_id` pair ensures a user can never submit multiple reviews for a single task.

### 5. Efficient Read Caching (Cache-Aside Pattern)

Searching for workers by skill and availability is a heavy database read operation. I implemented an asynchronous Redis caching layer to store search results using structured composite keys.

- **Graceful Degradation:** Wrapped the Redis logic in `try/except` blocks so that if the cache service goes down, the app automatically falls back to PostgreSQL without crashing.
- **Performance:** Brought query times down from **67.93 ms** to **5.20 ms** under stress testing.

---

##  Automated Testing Suite

I wrote an integration testing suite using **Pytest** and FastAPI's `TestClient` to ensure future changes don't break core workflows. The suite covers 8 critical end-to-end pipelines:

| # | Test | What It Covers |
|---|---|---|
| 1 | `test_api_health_check` | Verifies API and database connections are live |
| 2 | `test_user_registration_success` | Tests password hashing and validation during sign-up |
| 3 | `test_user_login_success` | Validates JWT token generation and expiry mechanics |
| 4 | `test_update_worker_profile_success` | Tests skill tagging and marketplace visibility |
| 5 | `test_job_booking_success` | Confirms customers can successfully dispatch bookings |
| 6 | `test_job_status_update_success` | Tests the strict job lifecycle states |
| 7 | `test_create_job_rating_success` | Ensures reviews open only after a successful completion |
| 8 | `test_job_deletion_and_safety_rules` | Confirms soft-deletes work and blocks unauthorized deletions |

### Running the Tests Locally

Since everything is containerized, you can run the full test suite with a single command:

```bash
docker compose exec api pytest test_main.py -v -s
```

---

##  How To Run

### 1. Setup Environment File

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user_name:your_password@db:5432/db_name
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Launch Containers

```bash
docker compose up --build
```

Once the containers are healthy, access the interactive Swagger documentation at:

👉 **http://localhost:8000/docs**

---

## ✍️ The Docker Chronicles

This project serves as a practical foundation for a technical blog series exploring containerization, databases, and clean code. Check out my latest articles on [Dev.to](https://dev.to/fjr) and [Hashnode](https://hashnode.com/@fjr).

---

**Built by Fajar** — a backend engineer focused on Python and distributed systems.
Find me on GitHub: [github.com/syeda-fajar](https://github.com/syeda-fajar)
