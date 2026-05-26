import uuid
import time
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.rag.chatbot import ask_chatbot
from app.utils.logger import logger

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    query: str
    response: str
    sources: List[str]
    conversation_id: str
    timestamp: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    
    conversation_id = request.conversation_id
    if not conversation_id or conversation_id.strip() == "":
        conversation_id = str(uuid.uuid4())
        logger.info(f"Generated new conversation_id: {conversation_id}")
        
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    logger.info(f"Processing chat request for session '{conversation_id}'")
    
    response_text, sources = await ask_chatbot(query, conversation_id)
    
    duration = time.time() - start_time
    logger.info(f"Finished processing query in {duration:.2f}s for session '{conversation_id}'")
    
    return ChatResponse(
        query=query,
        response=response_text,
        sources=sources,
        conversation_id=conversation_id,
        timestamp=datetime.now(timezone.utc).isoformat()
    )