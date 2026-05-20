# 🚀 LabourConnect:  Service Marketplace

LabourConnect was built to solve a common issue in local service markets: the lack of a reliable way to verify worker availability and trust their ratings. This is a FastAPI-based backend that handles the logic of connecting customers with skilled laborers while preventing common marketplace frauds like duplicate bookings and fake reviews.

---

## ✅ Core Features

* **Secure Authentication:** JWT-based login and registration with Role-Based Access Control (RBAC).
* **Multi-Role Profiles:** Separate, specialized profile management for Customers and Workers.
* **Skill Management:** Dynamic skill tagging (e.g., Electrician, Plumber) with a many-to-many relationship mapping.
* **Real-time Availability:** One-toggle availability system that reflects a worker's current state to potential customers.
* **Smart Search & Filtering:** API-level filtering to find workers by specific skills and current availability.
* **Booking State Machine:** A governed lifecycle for jobs (Pending → Accepted → In-Progress → Completed).
* **Historical Pricing Engine:** Implemented an hourly rate system backed by a robust pricing snapshot engine to preserve financial contract histories securely across profile updates.
* **Automated Rating System:** Secure feedback loop with pre-calculated average ratings for high-performance lookups.
* **Duplicate Prevention:** Backend logic to prevent multiple active bookings for the same worker-customer pair.
* **Automated Availability Lifecycle:** System automatically hides workers from search results upon job acceptance and restores "Available" status upon customer-confirmed completion to reduce operational friction.

---

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python 3.10+)
* **Database:** PostgreSQL (with SQLAlchemy ORM)
* **In-Memory Store:** Redis 7 (Alpine) for high-speed read caching
* **Migrations:** Alembic for version-controlled database schemas
* **Containerization:** Docker & Docker Compose
* **Security:** JWT (JSON Web Tokens) for Role-Based Access Control
* **Logic:** Pydantic for strict data validation

---

## 🏗️ System Architecture

The system follows a relational architecture designed for high data integrity. It utilizes a centralized `Users` table linked to a specialized `Worker_profile`, enabling a clean separation of roles. Core entities include `Jobs` (the state machine governing the workflow), `Skills` (managed via a many-to-many `Worker_skills` relationship), and a `Rating` system that utilizes database-level constraints to prevent duplicate or fraudulent feedback.

---


## 🧠 Key Engineering Decisions

### **1. Scalable Architecture & Data Modeling (Foundation)**
Before writing any business logic, I established a modular project structure. I designed a highly relational database using **SQLAlchemy** and implemented **Alembic** for version-controlled database migrations. This ensures the schema can evolve safely without data loss, and the codebase remains clean and maintainable as the platform scales.

### **2. Secure Identity & Role Management (Auth)**
To ensure clear boundaries within the marketplace, I implemented a strict Role-Based Access Control (RBAC) system using JWT. I designed the database to utilize a centralized `User` base model that branches out into specific `Worker` and `Customer` profiles. This prevents privilege escalation and guarantees that protected routes are only accessible to authorized accounts.

### **3. Time-Based Availability Engine**
Instead of static profiles, I engineered a dynamic availability system that handles constraints at both the application and database levels:

- **Background Expiry:** I evaluated lazy evaluation vs. background scheduling for availability expiry. I chose APScheduler to periodically update statuses, prioritizing read speed for search queries over perfect real-time accuracy.

- **The Database Shield:** To solve the "Double-Booking" problem—where a worker might simultaneously accept two requests—I implemented a PostgreSQL Partial Unique Index:
`CREATE UNIQUE INDEX idx_one_active_job ON jobs (worker_id) WHERE status IN ('accepted', 'in_progress');`
This ensures the database acts as the final gatekeeper, rejecting any attempt to overbook a worker.


### **4. Workflow State Machine**
To prevent "Logical Teleporting" (e.g., marking a job as completed before it’s accepted), I built a strict transition matrix for the booking lifecycle.

- **State Validation:**** Every status update is validated against its current state to ensure a predictable, legal path.

- **Atomic Updates:** Transitions are performed using SQLAlchemy's `.update()` with status-based filtering. By including the current status in the WHERE clause, the system protects against "Ghost Updates" from concurrent requests, ensuring a job is only updated if it remains in the expected state at the microsecond of execution.
### **5. Data Integrity & Trust Layer**
Because trust is the core of any marketplace, I designed the rating system defensively by handling several critical edge cases at both the application and database levels:

- **Lifecycle Enforcement:** Ratings are logically locked until a job reaches the completed state. This prevents "pre-emptive" or fake reviews for jobs that never happened.

- **Ownership Verification:** The system verifies that the currentUser is the exact customer who initiated the booking, preventing unauthorized users from tampering with a worker's reputation.

- **Identity Resolution (Anti-Self Rating):** To prevent self-promotion fraud, I implemented logic that resolves the underlying User_id behind a worker's profile. This ensures a worker cannot log in as a "Customer" and leave a 5-star review for themselves.

- **Unidirectional Logic:** By using specialized Role-Based Access Control (RBAC), the system strictly ensures only customers can initiate reviews, preventing workers from "retaliatory rating" or inflating their own stats.

- **Database-Level Finality:** I utilized a PostgreSQL UniqueConstraint on the (customer_id, job_id) pair. This acts as the final gatekeeper, making duplicate or spam reviews mathematically impossible even if the API layer is bypassed.

### **6. Audit-Ready Soft Deletion Pattern**
To balance user privacy with business intelligence, I implemented a Soft Delete pattern for jobs and user profiles.

- **Non-Destructive Schema:** Instead of DELETE commands, the system utilizes an is_deleted flag. This ensures that historical job data—crucial for financial auditing and dispute resolution—remains available in the database while being filtered out of active API queries.


### **7. Standardized Exception Architecture**
I moved away from generic 404/400 errors to a Standardized Error Schema. By building a custom `LabourConnectException` class and a Global Exception Handler, every error now returns a consistent JSON object:

* **Machine-Readable Codes:** Unique codes (e.g., BookingConflict, SelfRatingForbidden) allow frontend applications to trigger specific UI logic without parsing text strings.

* **Unified Response Format:** This ensures that whether a user hits a 404 or a complex business logic error, the API response structure is predictable and professional.

### **8. High-Performance Read Caching (Cache-Aside Pattern)**
To decouple high-traffic user searches from the primary PostgreSQL instance, I implemented an asynchronous Redis caching layer:

- **Deterministic Composites:** Cache keys are uniformly generated based on sanitized query parameters (search:skill:location:page:size:availability).

- **Pydantic Serialization:** Leveraged FastAPI's native jsonable_encoder to rapidly transform structured ORM relational maps into clean, storage-friendly text blocks.

- **Fault-Tolerant Fallbacks:** Wrapped all operations inside robust try/except patterns. If the memory cache undergoes temporary network failure or downtime, traffic transparently degrades gracefully back to PostgreSQL without interrupting user experience.

- **Proven Performance Gain:** Benchmarking showed a massive 11x latency reduction, dropping database lookup processing from 67.93 ms down to a blazing fast 5.20 ms (a 92.3% decrease).

---
## ⚠️ Known Limitations & Engineering Trade-offs
This project involved intentional compromises to focus on core backend logic.


* **Advanced Search Capabilities:** While basic search performance was significantly optimized using native PostgreSQL GIN Trigram indexes (pg_trgm) to handle swift partial string filtering, the architecture lacks a fully decentralized indexing cluster (such as Elasticsearch or Meilisearch) for complex semantic stemming or custom relevancy weighting.

* **State Synchronization:** Availability updates are currently request-driven. The system lacks a real-time layer (WebSockets) to push status changes to the frontend, meaning users might occasionally see stale "available" tags until they attempt a booking.

* **Rating Simplicity:** The trust layer assumes a single, final submission per job. There is currently no support for rating "Edit History" or a dispute resolution workflow, which would be essential for a real-world labor marketplace.

---

##  Automated Testing Suite

To ensure the reliability of the marketplace logic, role boundaries, and state transitions, the system features a robust automated integration test suite built with **Pytest** and `TestClient`. 

The suite covers **8 critical architectural pipelines**, verifying both "happy paths" and defensive security boundaries:

1. **`test_api_health_check`**: Asserts the live status of the API and verifies that background workers (such as the availability cleanup janitor) spin up correctly.
2. **`test_user_registration_success`**: Confirms role-based registration (`worker` vs. `customer`) handles password hashing securely.
3. **`test_user_login_success`**: Validates JWT generation, payload structure, and token expiration windows.
4. **`test_update_worker_profile_success`**: Verifies profile mutation, skill taxonomy mapping, and initial marketplace visibility toggles.
5. **`test_job_booking_success`**: Tests the initial booking transaction, verifying payload validation and the generation of the atomic job record.
6. **`test_job_status_update_success`**: Validates the strict multi-role state machine transitions (`pending` → `accepted` → `in_progress`).
7. **`test_create_job_rating_success`**: Simulates the full workflow lifecycle to unlock the trust layer, ensuring ratings can only be calculated once a customer marks a job as `completed`.
8. **`test_job_deletion_and_safety_rules`**: Validates edge cases and prevents security vulnerabilities (e.g., ensuring workers cannot delete jobs, and customers cannot cancel jobs once work has been accepted).

### Running the Tests Locally

Since the entire system is containerized, you can spin up an isolated test database session and execute the full suite with a single command:


`docker compose exec api pytest test_main.py -v -s`
- **Expected Output Structure**
```bash
======================= test session starts =======================
platform linux -- Python 3.10.20, pytest-8.1.1
rootdir: /app
plugins: anyio-4.13.0
collected 8 items

test_main.py::test_api_health_check PASSED
test_main.py::test_user_registration_success PASSED
test_main.py::test_user_login_success PASSED
test_main.py::test_update_worker_profile_success PASSED
test_main.py::test_job_booking_success PASSED
test_main.py::test_job_status_update_success PASSED
test_main.py::test_create_job_rating_success PASSED
test_main.py::test_job_deletion_and_safety_rules PASSED

======================= 8 passed in 5.42s =======================
```
## 🚀 How To Run

The entire environment is containerized for a "One-Command" setup. Follow these steps to get your local development environment ready:

### **1. Environment Configuration**
Before launching, you must create a `.env` file in the root directory. This file stores your secrets and database credentials safely. 

**Create a `.env` file and add the following:**
```env
DATABASE_URL=postgresql://your_db_user:your_db_password@db:5432/your_db_name
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
(Note: Ensure `.env` is added to your .gitignore to keep your secrets out of version control.)

**Launch with Docker Compose:**
Ensure you have Docker installed, then run the following command from the root folder:
`docker-compose up --build`
This command will automatically:

- Pull and spin up the official PostgreSQL 15 database engine.

- Launch a lightweight Redis 7 Alpine cache microservice.

- Automatically compile, configure dependencies, and expose your custom FastAPI application image.

- Wire them together inside an isolated, secure, private network layer sharing ports across local mappings (defaulting to 8000).

**Verify the Installation and API Docs**
Once the terminal logs confirm the containers are healthy, access the interactive documentation panel to test calls live:
👉 http://localhost:8000/docs


---

## 🗺️ Planned Features (Roadmap)

- **[ ] Real-time State Notifications:** Integrating a continuous WebSocket communication channel to stream live booking changes straight to mobile and web dashboards.

- **[ ] Automated Email Confirmations:** Integrating a background mail delivery server for immediate job status alerts and digital invoices.

---

## ✍️ The Docker Chronicles
This project is part of a technical blog series exploring containerization. 
Check out my latest articles on [Dev.to](https://dev.to/fjr) and [Hashnode](https://hashnode.com/@fjr).

**Built by Faja**r — a backend engineer focused on Python and distributed systems. Find me on GitHub (https://github.com/syeda-fajar).
