from fastapi import APIRouter, Body
from typing import Dict, Any
from backend.main import main_pipeline

router = APIRouter(
    prefix="/api",
    tags=["Pipelines"],
)

@router.put("/pipelines/{pipeline_id}/config")
async def update_pipeline_config(pipeline_id: str, config_update: Dict[str, Any] = Body(...)):
    """
    Updates the pipeline's configuration dynamically.
    This can be used to change sender host/port, or enable/disable features.

    Example body for features: `{"features": {"hands": false, "gaze": true}}`
    Example body for sender: `{"host": "192.168.1.100", "port": 12345}`
    """
    # In a multi-pipeline setup, pipeline_id would be used to select the instance.
    main_pipeline.update_config(config_update)
    return {
        "message": f"Configuration for pipeline {pipeline_id} updated.",
        "update_applied": config_update,
        "note": "Some configuration changes may require a pipeline restart to take full effect."
    }
