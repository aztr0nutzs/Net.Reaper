import asyncio
import json
import os
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
import subprocess
from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# -----------------------------------------------------------------------------
# NetReaper Remote Server (FastAPI)
#
# This module defines a FastAPI application that mirrors the CLI functionality
# of NetReaper for remote control via HTTP and WebSockets.  It is hardened
# relative to the original prototype by loading secrets from environment
# variables, issuing JWTs with expiration, validating tokens consistently
# across HTTP and WebSocket endpoints, and determining the working directory
# dynamically from the project root.
#
# To run the server:
#   uvicorn server.main:app --host 0.0.0.0 --port 8443
# -----------------------------------------------------------------------------

app = FastAPI(title="NetReaper Remote Server")

# Allow CORS for convenience.  In production, restrict origins appropriately.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for the GUI
app.mount("/static", StaticFiles(directory="gui"), name="static")

# Load secret key and admin password from environment with sensible defaults.
# A unique secret is generated if NETREAPER_SECRET_KEY is not set, ensuring
# tokens cannot be guessed across runs.  Similarly, the admin password
# defaults to "netreaper123" but should be overridden in production.
SECRET_KEY: str = os.getenv("NETREAPER_SECRET_KEY", uuid4().hex)
ADMIN_PASSWORD: str = os.getenv("NETREAPER_PASSWORD", "netreaper123")

# Store pairing sessions in memory.  A more robust implementation could
# persist this mapping or integrate with a database.
paired_sessions: dict[str, dict] = {}

def create_token(payload: dict, expires_in: int = 3600) -> str:
    """Generate a signed JWT with an expiration claim.

    Args:
        payload: Base claims to include in the token.  Must not contain
            an `exp` claim; one will be added based on `expires_in`.
        expires_in: Lifetime of the token in seconds (default: one hour).

    Returns:
        Encoded JWT string.
    """
    exp = datetime.utcnow() + timedelta(seconds=expires_in)
    claims = payload.copy()
    claims["exp"] = exp
    return jwt.encode(claims, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict | None:
    """Validate a JWT and return its decoded payload or None on failure."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.post("/auth")
async def authenticate(request: Request):
    """Authenticate a user and return a JWT.  Expects JSON {"password": "..."}."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    password = data.get("password")
    if not password or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_token({"user": "admin", "role": "admin"})
    return {"token": token}

@app.post("/pair")
def pair_device(deviceId: str, role: str):
    """Register a remote device and return a pairing code."""
    if role not in {"remote", "gui"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    code = uuid4().hex[:8].upper()
    paired_sessions[code] = {"device": deviceId, "role": role, "status": "paired"}
    return {"pairCode": code, "status": "paired"}

@app.post("/api/telemetry")
def telemetry(data: dict):
    """Receive telemetry data from clients.  Extend as needed."""
    print(f"Telemetry: {data}")
    return {"ok": True}

@app.post("/api/action")
def action(data: dict):
    """Handle action requests from clients.  Extend as needed."""
    print(f"Action: {data}")
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def get_gui():
    """Return the GUI index.html if it exists."""
    gui_path = Path("gui/index.html")
    return gui_path.read_text() if gui_path.exists() else HTMLResponse("<h1>GUI not found</h1>", status_code=404)

@app.get("/pair/{code}")
def query_pair(code: str):
    session = paired_sessions.get(code)
    if not session:
        raise HTTPException(status_code=404, detail="Pairing code not found")
    return session

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for remote command execution.

    The client must send a JSON object containing a `token` field as the first
    message.  The token is validated, and subsequent messages should contain
    JSON objects with a `command` field.  Output from the command is streamed
    back to the client line by line.  The working directory is the project
    root (determined relative to this file).
    """
    await websocket.accept()
    try:
        # Receive authentication token
        auth_msg = await websocket.receive_text()
        auth_json = json.loads(auth_msg)
        token = auth_json.get("token")
        payload = verify_token(token) if token else None
        if not payload:
            await websocket.send_text(json.dumps({"error": "Authentication failed"}))
            await websocket.close(code=1008)
            return
        await websocket.send_text(json.dumps({"status": "authenticated"}))
        # Determine project root (one level above this file)
        base_dir = Path(__file__).resolve().parents[1]
        # Loop to receive commands
        while True:
            data = await websocket.receive_text()
            cmd_json = json.loads(data)
            command = cmd_json.get("command")
            if not command:
                await websocket.send_text(json.dumps({"error": "No command provided"}))
                continue
            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    executable="/bin/bash",
                    cwd=str(base_dir),
                )
                await websocket.send_text(json.dumps({"output": f"Executing: {command}"}))
                assert process.stdout is not None
                # Stream output
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    await websocket.send_text(json.dumps({"output": line.decode().rstrip()}))
                rc = await process.wait()
                await websocket.send_text(json.dumps({"output": f"Return code: {rc}"}))
            except Exception as exc:
                await websocket.send_text(json.dumps({"error": f"Execution error: {str(exc)}"}))
    except Exception as exc:
        print(f"WebSocket error: {exc}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)