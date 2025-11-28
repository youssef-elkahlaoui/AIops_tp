import os
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()
ACTIVE_FILE = os.getenv("ACTIVE_FILE", "/data/active_version")  # contains "v1" or "v2"
BACKEND_MAP = {
    "v1": f"http://rag-backend-v1:{os.getenv('BACKEND_PORT_V1', '8101')}",
    "v2": f"http://rag-backend-v2:{os.getenv('BACKEND_PORT_V2', '8102')}",
}

class Query(BaseModel):
    query: str

def get_active_version():
    try:
        if os.path.exists(ACTIVE_FILE):
            with open(ACTIVE_FILE, "r") as f:
                v = f.read().strip()
                return v if v in BACKEND_MAP else "v1"
        return "v1"
    except Exception:
        return "v1"

@app.post("/chat")
async def chat(q: Query):
    active = get_active_version()
    backend_url = BACKEND_MAP[active] + "/chat"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(backend_url, json=q.dict())
            return r.json()
    except Exception as e:
        return {"error": str(e), "active_version": active}

@app.post("/activate")
def activate(version: str):
    if version not in BACKEND_MAP:
        return {"error": "unknown version"}
    with open(ACTIVE_FILE, "w") as f:
        f.write(version)
    return {"activated": version}
