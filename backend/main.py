"""
Intelligent Proctor — FastAPI Backend

Endpoints:
  POST /session/start   — Start a new session (proctor or deep-work)
  POST /session/stop    — End the active session, returns JSON report
  GET  /session/report  — Retrieve the last session's report
  WS   /ws/stream       — Real-time frame ingestion + metrics push
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO

from session_manager import SessionManager
from ws_handler import router as ws_router

# ---------------------------------------------------------------------------
# Resolve the YOLO model path (lives in project root, one level up)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
MODEL_PATH = os.path.join(PROJECT_ROOT, "best.pt")


# ---------------------------------------------------------------------------
# App lifespan — load the YOLO model once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[startup] Loading YOLO model from {MODEL_PATH} ...")
    vision_model = YOLO(MODEL_PATH)
    app.state.session_manager = SessionManager(vision_model)
    print("[startup] Model loaded. Ready.")
    yield
    print("[shutdown] Cleaning up.")


app = FastAPI(title="Intelligent Proctor API", lifespan=lifespan)

# -- CORS (allow the React dev server) --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- WebSocket routes --
app.include_router(ws_router)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    mode: str  # "PROCTOR" or "DEEP_WORK"


@app.post("/session/start")
async def start_session(req: StartSessionRequest):
    mgr: SessionManager = app.state.session_manager

    if mgr.is_active:
        return {"error": "A session is already active", "session_id": mgr.session_id}

    mode = req.mode.upper()
    if mode not in ("PROCTOR", "DEEP_WORK"):
        return {"error": f"Invalid mode: {req.mode}. Use PROCTOR or DEEP_WORK."}

    session_id = mgr.start_session(mode)
    return {"session_id": session_id, "mode": mode}


@app.post("/session/stop")
async def stop_session():
    mgr: SessionManager = app.state.session_manager

    if not mgr.is_active:
        return {"error": "No active session to stop"}

    report = mgr.stop_session()
    return report


@app.get("/session/report")
async def get_report():
    mgr: SessionManager = app.state.session_manager

    if mgr.last_report is None:
        return {"error": "No report available. Run a session first."}

    return mgr.last_report


@app.get("/health")
async def health():
    return {"status": "ok"}
