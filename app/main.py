# app/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from app.core.database import init_db
from app.services.ingestion import ingest_post, create_variant
from app.services.validater import ConstraintViolationError
from app.services.workflow import update_variant_status, schedule_variant, WorkflowError

app = FastAPI(title="Social Media Studio API")

@app.on_event("startup")
def startup_event():
    init_db()

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