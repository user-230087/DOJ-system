# Distributed Online Judge (OJ) System

A secure, scalable, and event-driven microservices-based Online Judge platform (similar to LeetCode or HackerRank) built using **Python (FastAPI)**, **Docker**, **Redis Streams**, and **PostgreSQL**.

---

## Architecture Overview

The system is decoupled into two independent microservices communicating asynchronously via **Redis Streams**:

1. **`problem-service` (Port 8080):** 
   * **Stateful API & Admin CRUD:** Manages questions, hidden test cases, and user submissions.
   * **Database:** Uses PostgreSQL (via SQLAlchemy) to persist entities.
   * **Event Producer/Consumer:** Pushes queued submissions to Redis Streams and listens for incoming verdicts to update database records asynchronously.
2. **`execution-service` (Port 8081):**
   * **Stateless Worker Engine:** Consumes queued jobs from Redis, executes user code inside isolated Docker containers, and publishes verdicts back.
   * **Design Patterns:** Implements the **Template Method** and **Strategy** patterns for clean, extensible language runtimes (Python, C++).
   * **Sandboxing:** Enforces strict OS-level container isolation (`--network=none`, memory caps, CPU limits, pids limits).

```text
[Solver / Client] 
      │
      ▼ (HTTP POST)
[problem-service (8080)] ──(XADD PENDING)──> [Redis Stream: oj:submissions:queued]
      │                                                   │
      └──(Returns PENDING instantly)                      ▼
                                            [execution-service (8081)]
                                                        │
                                            (Runs in Docker Sandbox)
                                                        │
                                                        ▼
[problem-service DB] <──(XADD Verdict)────── [Redis Stream: oj:verdicts:ready]
```

---

## Design Patterns Used

* **Strategy & Factory Pattern (`LanguageExecutorFactory`):** Encapsulates compilation and execution recipes per language, allowing new languages to be added without modifying core execution logic (Open/Closed Principle).
* **Template Method Pattern (`BaseLanguageExecutor`):** Centralizes the shared execution pipeline (temp directory handling, test iteration, timeout enforcement) while delegating language-specific hooks to subclasses.
* **Port-and-Adapter / Asynchronous Event Queue (Redis Streams):** Decouples HTTP request-response cycles from heavy compute tasks, providing fault tolerance, consumer group scaling, and durable message persistence.

---

## Getting Started & Local Setup

### Prerequisites
* Python 3.10+
* Docker installed and running on your host machine
* Redis Server installed and running (`redis-server`)
* PostgreSQL database running locally (`coderunner_db`)

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-username/online-judge-backend.git
cd online-judge-backend

python -m venv online_judge_env
source online_judge_env/bin/activate
```

### 2. Install Dependencies
Install dependencies for both services:
```bash
 pip install -r requirements.txt
```

### 3. Start Redis & PostgreSQL
Ensure your backing services are active:
```bash
# Start Redis
redis-server --daemonize yes

# Ensure PostgreSQL service is running and coderunner_db is created
```

---

## Running the Services

Open **two separate terminal windows**, activate your virtual environment in both, and start each microservice:

### Terminal 1: Start `execution-service` (Port 8081)
```bash
cd execution-service
# Pre-pulls Docker environments on startup and starts Redis worker loop
uvicorn main:app --port 8081 --reload
```

### Terminal 2: Start `problem-service` (Port 8080)
```bash
cd problem-service
uvicorn main:app --port 8080 --reload
```

---

## API Usage Examples

### 1. Create a Question (Admin)# Distributed Online Judge (OJ) System

A secure, scalable, and event-driven microservices-based Online Judge platform (similar to LeetCode or HackerRank) built using **Python (FastAPI)**, **Docker**, **Redis Streams**, and **PostgreSQL**.

---

## Architecture Overview

The system is decoupled into two independent microservices communicating asynchronously via **Redis Streams**:

1. **`problem-service` (Port 8080):** 
   * **Stateful API & Admin CRUD:** Manages questions, hidden test cases, and user submissions.
   * **Database:** Uses PostgreSQL (via SQLAlchemy) to persist entities.
   * **Event Producer/Consumer:** Pushes queued submissions to Redis Streams and listens for incoming verdicts to update database records asynchronously.
2. **`execution-service` (Port 8081):**
   * **Stateless Worker Engine:** Consumes queued jobs from Redis, executes user code inside isolated Docker containers, and publishes verdicts back.
   * **Design Patterns:** Implements the **Template Method** and **Strategy** patterns for clean, extensible language runtimes (Python, C++).
   * **Sandboxing:** Enforces strict OS-level container isolation (`--network=none`, memory caps, CPU limits, pids limits).

```text
[Solver / Client] 
      │
      ▼ (HTTP POST)
[problem-service (8080)] ──(XADD PENDING)──> [Redis Stream: oj:submissions:queued]
      │                                                   │
      └──(Returns PENDING instantly)                      ▼
                                            [execution-service (8081)]
                                                        │
                                            (Runs in Docker Sandbox)
                                                        │
                                                        ▼
[problem-service DB] <──(XADD Verdict)────── [Redis Stream: oj:verdicts:ready]
```

---

## Design Patterns Used

* **Strategy & Factory Pattern (`LanguageExecutorFactory`):** Encapsulates compilation and execution recipes per language, allowing new languages to be added without modifying core execution logic (Open/Closed Principle).
* **Template Method Pattern (`BaseLanguageExecutor`):** Centralizes the shared execution pipeline (temp directory handling, test iteration, timeout enforcement) while delegating language-specific hooks to subclasses.
* **Port-and-Adapter / Asynchronous Event Queue (Redis Streams):** Decouples HTTP request-response cycles from heavy compute tasks, providing fault tolerance, consumer group scaling, and durable message persistence.

---

## Getting Started & Local Setup

### Prerequisites
* Python 3.10+
* Docker installed and running on your host machine
* Redis Server installed and running (`redis-server`)
* PostgreSQL database running locally (`coderunner_db`)

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-username/online-judge-backend.git
cd online-judge-backend

python -m venv online_judge_env
source online_judge_env/bin/activate
```

### 2. Install Dependencies
Install dependencies for both services:
```bash
pip install -r requirements.txt
```

### 3. Start Redis & PostgreSQL
Ensure your backing services are active:
```bash
# Start Redis
redis-server --daemonize yes

# Ensure PostgreSQL service is running and coderunner_db is created
```

---

## Running the Services

Open **two separate terminal windows**, activate your virtual environment in both, and start each microservice:

### Terminal 1: Start `execution-service` (Port 8081)
```bash
cd execution-service
# Pre-pulls Docker environments on startup and starts Redis worker loop
uvicorn main:app --port 8081 --reload
```

### Terminal 2: Start `problem-service` (Port 8080)
```bash
cd problem-service
uvicorn main:app --port 8080 --reload
```

---

## API Usage Examples

### 1. Create a Question (Admin)
```bash
curl -X POST http://localhost:8080/api/admin/questions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sum of two numbers",
    "statement": "Read two integers, print their sum.",
    "difficulty": "EASY",
    "testCases": [
      {"input": "2 3\n", "expectedOutput": "5\n", "hidden": false},
      {"input": "10 20\n", "expectedOutput": "30\n", "hidden": true}
    ]
  }'
```

### 2. Submit a Solution (Solver)
Submissions return `PENDING` instantly, while the background worker processes the code asynchronously via Redis Streams.
```bash
curl -X POST http://localhost:8080/api/questions/1/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "User",
    "language": "PYTHON",
    "sourceCode": "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)"
  }'
```
*Response:* `{"id": 1, "questionId": 1, "userId": "User", "language": "PYTHON", "status": "PENDING"}`

### 3. Check Submission Verdict
Poll the submission status using its ID:
```bash
curl -X GET http://localhost:8080/api/submissions/1
```
*Response once processed:* `{"id": 1, "questionId": 1, "userId": "User", "language": "PYTHON", "status": "ACCEPTED"}`
```bash
curl -X POST http://localhost:8080/api/admin/questions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sum of two numbers",
    "statement": "Read two integers, print their sum.",
    "difficulty": "EASY",
    "testCases": [
      {"input": "2 3\n", "expectedOutput": "5\n", "hidden": false},
      {"input": "10 20\n", "expectedOutput": "30\n", "hidden": true}
    ]
  }'
```

### 2. Submit a Solution (Solver)
Submissions return `PENDING` instantly, while the background worker processes the code asynchronously via Redis Streams.
```bash
curl -X POST http://localhost:8080/api/questions/1/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "User",
    "language": "PYTHON",
    "sourceCode": "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)"
  }'
```
*Response:* `{"id": 1, "questionId": 1, "userId": "User", "language": "PYTHON", "status": "PENDING"}`

### 3. Check Submission Verdict
Poll the submission status using its ID:
```bash
curl -X GET http://localhost:8080/api/submissions/1
```
*Response once processed:* `{"id": 1, "questionId": 1, "userId": "User", "language": "PYTHON", "status": "ACCEPTED"}`

## Future Roadmap & Enhancements

### 1. JWT Authentication & Role-Based Access Control
* **Secure Endpoints:** Implement OAuth2 with Password Flow and JWT tokens to authenticate users.
* **Role Management:** Introduce user roles (`ADMIN` vs. `USER`) to secure administrative routes (such as `POST /api/admin/questions`) ensuring only authorized administrators can create or modify questions.

### 2. Frontend Integration
* **Modern UI:** Build a responsive single-page application using React or Next.js.
.