from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from app.core.database import init_db
from app.services.ingestion import ingest_post, create_variant
from app.services.validater import ConstraintViolationError
from app.services.workflow import update_variant_status, schedule_variant, WorkflowError
from app.services.publisher import execute_idempotent_publish
from app.services.scheduler import start_scheduler
from app.core.database import get_db_connection
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.services.generator import generate_variant_with_ollama, GroundingError
from app.services.validater import ConstraintViolationError
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.services.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    init_db()
    start_scheduler()
    yield

app = FastAPI(title="Social Media Studio API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serves the UI landing page."""
    return FileResponse(os.path.join("app", "static", "index.html"))

@app.get("/api/history")
def get_publish_history():
    """Returns full audit trail of publish attempts."""
    conn = get_db_connection()
    cur = conn.execute(
        """SELECT h.id, h.slot_id, h.variant_id, h.platform, h.status, 
                  h.response_payload, h.attempted_at 
           FROM publish_history h 
           ORDER BY h.attempted_at DESC"""
    )
    history = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"history": history}
# --- Request Models ---
class IngestRequest(BaseModel):
    title: str
    source_type: str  # 'url' or 'markdown'
    content: str

class VariantRequest(BaseModel):
    post_id: int
    platform: str
    content: str

class ScheduleRequest(BaseModel):
    variant_id: int
    scheduled_time: str

# --- Endpoints ---
@app.post("/api/posts", status_code=status.HTTP_201_CREATED)
def create_post_endpoint(payload: IngestRequest):
    post_id = ingest_post(payload.title, payload.source_type, payload.content)
    return {"message": "Post ingested successfully", "post_id": post_id}

@app.post("/api/variants", status_code=status.HTTP_201_CREATED)
def generate_variant_endpoint(payload: VariantRequest):
    try:
        res = create_variant(payload.post_id, payload.platform, payload.content)
        return res
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

@app.patch("/api/variants/{variant_id}/status")
def review_variant_endpoint(variant_id: int, status_value: str):
    try:
        return update_variant_status(variant_id, status_value)
    except WorkflowError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/api/schedule")
def schedule_variant_endpoint(payload: ScheduleRequest):
    try:
        return schedule_variant(payload.variant_id, payload.scheduled_time)
    except WorkflowError as e:
        # Returns 400 Bad Request if unapproved
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/api/schedule/{slot_id}/publish")
async def trigger_publish_endpoint(slot_id: int):
    return await execute_idempotent_publish(slot_id)

class AIGenerateRequest(BaseModel):
    post_id: int
    platform: str
    source_content: str

@app.post("/api/variants/ai-generate", status_code=201)
def generate_ai_variant_endpoint(payload: AIGenerateRequest):
    try:
        res = generate_variant_with_ollama(
            post_id=payload.post_id,
            source_content=payload.source_content,
            platform=payload.platform
        )
        return res
    except GroundingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConstraintViolationError as e:
        raise HTTPException(status_code=422, detail=str(e))