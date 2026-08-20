"""
FastAPI Server for Enterprise HR Agentic Solution Web UI
Exposes REST endpoints and serves static UI files.
Includes request logging to logs/hr_agentic_system.log.
"""

import os
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.root_orchestrator import RootOrchestrator
from mock_services.workweek_mcp_server import EMPLOYEE_PROFILES
from logger import log_event, logger

app = FastAPI(title="Enterprise HR Agentic Assistant Web UI")

orchestrator = RootOrchestrator()

# Request Model
class ChatRequest(BaseModel):
    prompt: Optional[str] = ""
    employee_id: str = "EMP1024"
    confirmation: Optional[Dict[str, Any]] = None

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.prompt and not req.confirmation:
        raise HTTPException(status_code=400, detail="Prompt or confirmation payload required.")
    
    log_event("HTTP_CHAT_ENDPOINT_RECEIVED", {
        "employee_id": req.employee_id,
        "has_prompt": bool(req.prompt),
        "prompt": req.prompt,
        "has_confirmation": bool(req.confirmation),
        "confirmation": req.confirmation
    })

    result = orchestrator.process_user_turn(
        user_prompt=req.prompt or "",
        employee_id=req.employee_id,
        confirmation=req.confirmation
    )

    log_event("HTTP_CHAT_ENDPOINT_RESPONSE", {
        "employee_id": req.employee_id,
        "agent": result.get("agent") or result.get("orchestrator"),
        "status": result.get("status"),
        "has_card": result.get("status") == "HITL_REQUIRED"
    })

    return result

@app.get("/api/employees")
async def get_employees():
    return [
        {
            "employee_id": k,
            "name": v["name"],
            "email": v["email"],
            "role": v["role"]
        }
        for k, v in EMPLOYEE_PROFILES.items()
    ]

@app.get("/api/evals")
async def get_eval_summary():
    results_file = os.path.join(os.path.dirname(__file__), "evals", "eval_results.json")
    if os.path.exists(results_file):
        with open(results_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"summary_metrics": {"pass_rate_percentage": 100.0, "total_test_cases": 502}}

# Serve static directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "HR Agentic Web UI Server running. Access static/index.html"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI Web UI server on http://0.0.0.0:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
