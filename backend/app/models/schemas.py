from pydantic import BaseModel
from typing import Optional, Dict

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    disease: Optional[str] = None
    query: str
    location: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    data: Dict   # ✅ REQUIRED


class SessionCreateResponse(BaseModel):
    session_id: str