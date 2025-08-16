"""Shared application state, including singleton processing pipeline."""
from backend.pipeline import ProcessingPipeline

# In a real application, configuration would likely be loaded from a database or file
default_config = {
    "camera_index": 0,
    "fps": 30,
    "host": "127.0.0.1",
    "port": 39539,
    "features": {
        "pose": True,
        "hands": True,
        "face": True,
        "shrug": True,
        "gaze": True,
    },
}

# Singleton pipeline instance used throughout the application
main_pipeline = ProcessingPipeline(config=default_config)
