import asyncio
import json
import jwt
from uuid import uuid4
import subprocess
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="NetReaper Remote Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for GUI
app.mount("/static", StaticFiles(directory="gui"), name="static")

SECRET_KEY = "netreaper-secret-key-2025"  # Change in production
paired_sessions: dict[str, dict] = {}

def create_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.post("/auth")
def authenticate(password: str):
    if password == "netreaper123":
        token = create_token({"user": "admin", "exp": None})
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.post("/pair")
def pair_device(deviceId: str, role: str):
    if role not in {"remote", "gui"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    pair_code = uuid4().hex[:8].upper()
    paired_sessions[pair_code] = {
        "device": deviceId,
        "role": role,
        "status": "paired"
    }
    return {"pairCode": pair_code, "status": "paired"}

@app.post("/api/telemetry")
def telemetry(data: dict):
    # Log telemetry data
    print(f"Telemetry: {data}")
    return {"ok": True}

@app.post("/api/action")
def action(data: dict):
    # Handle action, perhaps log or trigger something
    print(f"Action: {data}")
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def get_gui():
    gui_path = Path("gui/index.html")
    if gui_path.exists():
        return gui_path.read_text()
    return HTMLResponse("<h1>GUI not found</h1>", status_code=404)

@app.get("/pair/{code}")
def query_pair(code: str):
    session = paired_sessions.get(code)
    if not session:
        raise HTTPException(status_code=404, detail="Pairing code not found")
    return session

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        auth_data = await websocket.receive_text()
        auth_json = json.loads(auth_data)
        token = auth_json.get("token")
        if not token or token != "netreaper123":
            await websocket.send_text(json.dumps({"error": "Authentication failed"}))
            await websocket.close(code=1008)
            return

        await websocket.send_text(json.dumps({"status": "authenticated"}))

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
                    cwd="/home/aztr0nutzs/Documents/Net.Reaper-1"
                )
                await websocket.send_text(json.dumps({"output": f"Executing: {command}"}))
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    await websocket.send_text(json.dumps({"output": line.decode().rstrip()}))
                return_code = await process.wait()
                await websocket.send_text(json.dumps({"output": f"Return code: {return_code}"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"error": f"Execution error: {str(e)}"}))
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)  # , ssl_keyfile="key.pem", ssl_certfile="cert.pem")
