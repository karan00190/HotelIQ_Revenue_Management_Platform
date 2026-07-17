from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services import knowledge_service
from app.services.assistant_service import (
    AssistantConfigError,
    AssistantProviderError,
    current_model_spec,
    is_configured,
    run_chat,
)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    history = [{"role": h.role, "content": h.content} for h in payload.history]
    try:
        return run_chat(db, payload.message, history)
    except AssistantConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except AssistantProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get("/status")
def get_status():
    return {
        "configured": is_configured(),
        "model": current_model_spec(),
        "knowledge_available": knowledge_service.is_available(),
        "knowledge_chunks": knowledge_service.chunk_count(),
    }
