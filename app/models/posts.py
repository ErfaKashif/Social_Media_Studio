from pydantic import BaseModel, Field
from typing import Optional

class PostCreate(BaseModel):
    title: str = Field(..., example="Capstone Launch")
    source_type: str = Field(..., example="markdown")
    content: str = Field(..., example="Full post content goes here.")

class PostResponse(BaseModel):
    post_id: int
    title: str
    source_type: str
    content: str
    created_at: Optional[str] = None