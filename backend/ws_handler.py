"""
WebSocket handler — receives frames from the browser, pipes them through
SessionManager, and pushes metrics back.
"""

import json
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# The session_manager instance is injected from main.py via app.state
# We access it through the websocket's app reference.


@router.websocket("/ws/stream")
async def stream_handler(websocket: WebSocket):
    await websocket.accept()
    session_mgr = websocket.app.state.session_manager

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)

            if message.get("type") != "frame":
                await websocket.send_json({"type": "error", "message": "Unknown message type"})
                continue

            if not session_mgr.is_active:
                await websocket.send_json({"type": "error", "message": "No active session"})
                continue

            b64_data = message.get("data", "")
            metrics = session_mgr.process_frame(b64_data)
            await websocket.send_json(metrics)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
