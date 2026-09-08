# BUILDLOG.md

## AI Collaboration & Engineering Log

This document tracks where AI assistance was utilized throughout the development of **Social Media Studio**, where configuration or logical issues occurred, and the manual adjustments made to ensure a resilient system.

---

### 1. Ingestion & Variant Generator

* **AI Assistance**: Used AI to draft initial FastAPI CRUD route handlers and construct string-parsing templates for blog post ingestion.
* **Issues Encountered**: The initial AI-generated generator script relied on external paid APIs (OpenAI/Gemini), violating the strict $0 budget constraint.


* **Manual Adjustments**:
* Integrated local **Ollama (`llama3.2:3b`)** via `httpx` to execute completely offline text generation with zero credit-card dependencies.


* Added a custom `verify_grounding` function using regex checks to catch and reject hallucinated numbers/statistics not present in the original source post.





---

### 2. Configuration & Virtual Environment Setup

* **AI Assistance**: Generated configuration models using Pydantic `BaseSettings`.
* **Issues Encountered**:
* Pydantic V2 threw `PydanticDeprecatedSince20` deprecation warnings for `class Config` syntax.
* Uvicorn threw `ModuleNotFoundError: No module named 'apscheduler'` when booting child worker processes.


* **Manual Adjustments**:
* Refactored `app/core/config.py` to use `model_config = ConfigDict(env_file=".env")` for clean Pydantic v2 compliance.
* Replaced heavy `APScheduler` external dependencies with a lightweight, zero-dependency background worker running on native `asyncio.create_task()` and SQLite polling.



---

### 3. Architecture & Review Workflow

* **AI Assistance**: Drafted database migration scripts and state-machine transitions (`draft` $\rightarrow$ `approved` $\rightarrow$ `published`).


* **Issues Encountered**: The workflow service initially allowed scheduling posts in past dates and failed to block draft variants when requested directly via API payloads.
* **Manual Adjustments**:
* Added explicit status checks in `app/services/workflow.py` to raise HTTP `400 Bad Request` if `status != 'approved'`.


* Added datetime validation (`scheduled_dt < datetime.now()`) to enforce future-only scheduling.



---

### 4. Adapter Pattern & Idempotency Engine

* **AI Assistance**: Designed the `SocialPublisher` abstract interface and concrete Discord/Mock class structures.


* **Issues Encountered**: High-concurrency or retried API triggers created duplicate entries in `publish_history` when background workers ran simultaneously.
* **Manual Adjustments**:
* Implemented a composite idempotency key (`variant_{id}_time_{timestamp}`).


* Enforced SQLite unique constraint guards on the `idempotency_key` column inside `schedule_slots` so retried executions safely return `status: ignored` without duplicate posting.





---

### 5. Testing & Environment Paths

* **AI Assistance**: Generated test cases using `pytest` and FastAPI's `TestClient`.


* **Issues Encountered**:
* Running `pytest` directly threw `ModuleNotFoundError: No module named 'app'` due to missing path resolution.
* Fastapi log outputs displayed `@app.on_event("startup")` deprecation warnings.


* **Manual Adjustments**:
* Configured `conftest.py` in the project root to automatically append `sys.path`.
* Migrated `app/main.py` startup hooks to FastAPI's modern `@asynccontextmanager` `lifespan` handler.