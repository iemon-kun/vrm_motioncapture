from fastapi import APIRouter
from pydantic import BaseModel
from backend.main import main_pipeline

router = APIRouter(
    prefix="/api",
    tags=["Replay"],
)

class ReplayRequest(BaseModel):
    filepath: str

@router.post("/replay/{pipeline_id}/start")
async def start_replay(pipeline_id: str, request: ReplayRequest):
    # This will stop the live pipeline and start replaying.
    # A more advanced implementation might manage multiple pipeline instances.
    main_pipeline.start_replay(filepath=request.filepath)
    return {"message": f"Replay started for pipeline {pipeline_id} from {request.filepath}. Note: This requires a pipeline restart to take effect if already running."}

@router.post("/replay/{pipeline_id}/stop")
async def stop_replay(pipeline_id: str):
    main_pipeline.stop_replay()
    return {"message": f"Stopped replay for pipeline {pipeline_id}. Note: This requires a pipeline restart to return to live mode."}
