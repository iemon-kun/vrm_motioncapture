from fastapi import APIRouter, Body
from pydantic import BaseModel
from backend.state import main_pipeline

router = APIRouter(
    prefix="/api",
    tags=["Recording"],
)

class RecordRequest(BaseModel):
    filepath: str
    format: str = "jsonl"

@router.post("/record/{pipeline_id}/start")
async def start_recording(pipeline_id: str, request: RecordRequest):
    # Note: pipeline_id is part of the API path but not yet used in the backend logic
    # as we only have one main pipeline instance.
    main_pipeline.start_recording(filepath=request.filepath, fmt=request.format)
    return {"message": f"Recording started for pipeline {pipeline_id} to {request.filepath}"}

@router.post("/record/{pipeline_id}/stop")
async def stop_recording(pipeline_id: str):
    main_pipeline.stop_recording()
    return {"message": f"Stopped recording for pipeline {pipeline_id}"}
