# Social Media Studio

Social Media Studio is a backend service built with FastAPI and SQLite that converts blog posts into multi-platform social media campaigns. The system creates platform-specific variants, enforces length and hashtag constraints, requires explicit human review before scheduling, and publishes content using an idempotent architecture to guarantee zero duplicate posts.

---

## Architecture

```text
[Blog Post: URL / Markdown]
         │
         ▼
 1. Post Ingestion (SQLite Store)
         │
         ▼
 2. Variant Generator (Ollama / Hand-written)
         │
         ▼
 3. Constraint & Grounding Validation Guard
         │
         ▼
 4. Review Workflow (draft ──> approved / rejected)
         │
         ▼
 5. Durable Background Worker / Scheduler
         │
         ▼
 6. SocialPublisher Interface (Adapter Layer)
    ├── Discord Webhook Adapter (Real Target)
    ├── Mock X Adapter
    └── Mock LinkedIn Adapter
         │
         ▼
 7. Idempotent Publish & Audit Trail History

```

---

## Tech Stack & $0 Constraints

* **Language & Framework**: Python 3.13 / FastAPI


* **Database**: SQLite (Zero-configuration persistence)


* **AI Text Generation**: Local Ollama (`llama3.2:3b`) — 100% free, $0 cost, zero credit card requirement


* **Target Adapters**: Discord Webhook (Real Target), Mock X, Mock LinkedIn


* **Automated Testing**: `pytest` + `httpx`


---

## Setup & Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/YOUR_USERNAME/flyrank-capstone-social-studio.git
cd flyrank-capstone-social-studio

```

### 2. Create and Activate Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt

```

### 4. Set Up Environment Variables

Copy `.env.example` to `.env`:

```powershell
cp .env.example .env

```

Ensure your `.env` contains:

```text
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your_webhook_here"
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"

```

---

## Running the Application

### Start the FastAPI Backend Server

```powershell
python -m uvicorn app.main:app --reload

```

* **Interactive API Documentation (Swagger)**: Access at `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`
* **Frontend Dashboard Interface**: Access at `[http://127.0.0.1:8000/](http://127.0.0.1:8000/)`

---

## API Endpoints Summary

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/posts` | Ingest Markdown text or URL source content.

 |
| `POST` | `/api/variants` | Draft a manual platform-specific variant with rule validation.

 |
| `POST` | `/api/variants/ai-generate` | Generate grounded variants using local Ollama (`llama3.2:3b`).

 |
| `PATCH` | `/api/variants/{id}/status` | Update workflow status (`draft`, `approved`, `rejected`).

 |
| `POST` | `/api/schedule` | Queue approved variants for future publication slots.

 |
| `POST` | `/api/schedule/{slot_id}/publish` | Trigger idempotent publication execution.

 |
| `GET` | `/api/history` | Retrieve complete publication audit history.

 |

---

## Running Tests

Execute the automated `pytest` suite covering constraint violations, workflow guards, past-date protections, Ollama grounding checks, and idempotency retries:

```powershell
python -m pytest -v

```