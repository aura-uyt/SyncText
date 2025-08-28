import asyncio
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict, Set
import json
import uuid

# Create FastAPI app
app = FastAPI(title="SyncText API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# In-memory storage (use Redis in production)
documents: Dict[str, dict] = {}
user_sessions: Dict[str, dict] = {}

@app.get("/")
async def root():
    return {"message": "SyncText API is running"}

@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    if doc_id not in documents:
        documents[doc_id] = {
            "content": "",
            "users": set(),
            "version": 0
        }
    return {
        "id": doc_id,
        "content": documents[doc_id]["content"],
        "version": documents[doc_id]["version"]
    }

@sio.event
async def connect(sid, environ):
    print(f"User connected: {sid}")
    user_sessions[sid] = {
        "id": sid,
        "document_id": None,
        "cursor_position": 0
    }

@sio.event
async def disconnect(sid):
    print(f"User disconnected: {sid}")
    if sid in user_sessions:
        doc_id = user_sessions[sid].get("document_id")
        if doc_id and doc_id in documents:
            documents[doc_id]["users"].discard(sid)
        del user_sessions[sid]

@sio.event
async def join_document(sid, data):
    doc_id = data.get("document_id")
    if not doc_id:
        return
    
    # Initialize document if it doesn't exist
    if doc_id not in documents:
        documents[doc_id] = {
            "content": "",
            "users": set(),
            "version": 0
        }
    
    # Add user to document
    documents[doc_id]["users"].add(sid)
    user_sessions[sid]["document_id"] = doc_id
    
    # Send current document state to the user
    await sio.emit('document_state', {
        "content": documents[doc_id]["content"],
        "version": documents[doc_id]["version"]
    }, room=sid)
    
    # Notify other users about new participant
    await sio.emit('user_joined', {
        "user_id": sid,
        "total_users": len(documents[doc_id]["users"])
    }, room=doc_id, skip_sid=sid)

@sio.event
async def text_change(sid, data):
    doc_id = user_sessions[sid].get("document_id")
    if not doc_id or doc_id not in documents:
        return
    
    # Update document content
    new_content = data.get("content", "")
    operation = data.get("operation", {})
    
    documents[doc_id]["content"] = new_content
    documents[doc_id]["version"] += 1
    
    # Broadcast changes to other users
    await sio.emit('text_change', {
        "content": new_content,
        "operation": operation,
        "version": documents[doc_id]["version"],
        "user_id": sid
    }, room=doc_id, skip_sid=sid)

@sio.event
async def cursor_change(sid, data):
    doc_id = user_sessions[sid].get("document_id")
    if not doc_id:
        return
    
    position = data.get("position", 0)
    user_sessions[sid]["cursor_position"] = position
    
    # Broadcast cursor position to other users
    await sio.emit('cursor_change', {
        "user_id": sid,
        "position": position
    }, room=doc_id, skip_sid=sid)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)