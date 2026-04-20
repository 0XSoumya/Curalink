from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SessionCreateResponse
from app.core.database import get_db
from app.graph.graph_builder import build_graph
from datetime import datetime
import uuid

router = APIRouter(prefix="")
graph = build_graph()


@router.post("/session", response_model=SessionCreateResponse)
async def create_session():
    db = get_db()
    session_id = str(uuid.uuid4())

    await db.sessions.insert_one({
        "session_id": session_id,
        "chat_history": [],
        "top_docs": [],
        "buffer_docs": [],
        "clinical_trials": [],
        "disease": None,
        "last_query": None,
        "updated_at": datetime.utcnow(),
    })

    return {"session_id": session_id}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    db = get_db()

    if not request.session_id:
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "chat_history": [],
            "top_docs": [],
            "buffer_docs": [],
            "clinical_trials": [],
            "disease": request.disease,
            "last_query": request.query,
            "updated_at": datetime.utcnow(),
        }
        await db.sessions.insert_one(session_data)
    else:
        session_id = request.session_id
        session_data = await db.sessions.find_one({"session_id": session_id})
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

    state = {
        "query": request.query,
        "disease": request.disease,
        "location": request.location,
        "chat_history": session_data["chat_history"],
        "session_id": session_id,
        "top_docs": session_data.get("top_docs", []),
        "buffer_docs": session_data.get("buffer_docs", []),
        "clinical_trials": session_data.get("clinical_trials", [])
    }

    result = await graph.ainvoke(state)

    response_data = result.get("final_output", {})
    response_text = response_data.get("overview", "No response generated")

    await db.sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "top_docs": result.get("top_docs", []),
                "buffer_docs": result.get("buffer_docs", []),
                "clinical_trials": result.get("clinical_trials", []),
                "last_query": request.query,
                "updated_at": datetime.utcnow(),
            },
            "$push": {
                "chat_history": {
                    "query": request.query,
                    "response": response_text,
                    "full_data": response_data # 🔥 CRITICAL: Save the rich data so old chats load properly
                }
            },
        },
    )

    return {
        "session_id": session_id,
        "message": response_text,
        "data": response_data
    }


# 🔥 NEW: Fetch list of recent sessions
@router.get("/sessions")
async def get_sessions():
    db = get_db()
    # Fetch top 20 most recent sessions
    cursor = db.sessions.find(
        {"last_query": {"$ne": None}}, # Only fetch sessions where the user actually typed something
        {"session_id": 1, "last_query": 1, "updated_at": 1}
    ).sort("updated_at", -1).limit(20)
    
    sessions = await cursor.to_list(length=20)
    
    return [
        {
            "session_id": s["session_id"],
            "title": s.get("last_query", "New Chat"),
            "updated_at": s.get("updated_at")
        }
        for s in sessions
    ]


# 🔥 NEW: Fetch full history for a specific session
@router.get("/session/{session_id}")
async def get_session(session_id: str):
    db = get_db()
    session_data = await db.sessions.find_one({"session_id": session_id})
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_data["session_id"],
        "chat_history": session_data.get("chat_history", [])
    }