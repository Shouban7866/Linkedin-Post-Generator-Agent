from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from langgraph.types import Command
from agent_graph import agent_app

app = FastAPI(title="LinkedIn Agent Backend Server")

class StartRequest(BaseModel):
    topic: str
    thread_id: str

class FeedbackRequest(BaseModel):
    user_action: str
    thread_id: str

def format_state_response(config: dict) -> Dict[str, Any]:
    state_snapshot = agent_app.get_state(config)
    values = state_snapshot.values

    is_paused = "human_review" in state_snapshot.next

    interrupt_data = None
    if is_paused and state_snapshot.tasks:
        active_task = state_snapshot.tasks[0]
        if active_task.interrupts:
            interrupt_data = active_task.interrupts[0].value

    return {
        "is_paused": is_paused,
        "interrupt_data": interrupt_data,
        "draft": values.get("draft", ""),
        "attempt": values.get("attempt", 0),
        "is_approved": values.get("is_approved", False),
        "api_status": values.get("api_status", "")
    }

@app.post("/start")
def start_workflow(req: StartRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    initial_state = {
        "topic": req.topic,
        "draft": "",
        "review_feedback": "",
        "is_approved": False,
        "attempt": 0,
        "api_status": ""
    }
    try:
        agent_app.invoke(initial_state, config=config)
        return format_state_response(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit_feedback")
def submit_feedback(req: FeedbackRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    try:
        agent_app.invoke(Command(resume=req.user_action), config=config)
        return format_state_response(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
