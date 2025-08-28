# SyncText - Real-time Collaborative Text Editor

A Python-based real-time collaborative text editor using FastAPI and Socket.IO.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the server:**
```bash
python main.py
```

3. **Open the client:**
Open `client.html` in multiple browser tabs to test collaboration.

## Architecture

- **Backend:** FastAPI + Socket.IO for WebSocket handling
- **Real-time sync:** Event-driven text synchronization
- **Storage:** In-memory (upgrade to Redis for production)

## API Endpoints

- `GET /` - Health check
- `GET /document/{doc_id}` - Get document content
- WebSocket events: `join_document`, `text_change`, `cursor_change`

## Next Steps

1. Add operational transform for conflict resolution
2. Implement user authentication
3. Add Redis for scalable document storage
4. Build React frontend for better UX
5. Add document persistence with PostgreSQL