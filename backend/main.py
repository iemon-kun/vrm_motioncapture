import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.api import pipelines, record, replay, receiver
from backend.state import main_pipeline


# --- FastAPI App ---
app = FastAPI(
    title="VRM MotionCapture",
    description="A server for motion capture using VRM, OSC, and VMC protocols.",
    version="0.1.0",
)

# Serve the simple frontend for manual testing/debugging
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.on_event("startup")
def startup_event():
    """Start the processing pipeline in a background thread."""
    pipeline_thread = threading.Thread(target=main_pipeline.run, daemon=True)
    pipeline_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    """Stop the processing pipeline."""
    if main_pipeline.is_running:
        main_pipeline.stop()

# Include API routers
app.include_router(pipelines.router)
app.include_router(record.router)
app.include_router(replay.router)
app.include_router(receiver.router)


@app.get("/")
async def read_root():
    """
    Root endpoint to check if the server is running.
    """
    return {"message": "Welcome to VRM MotionCapture API", "pipeline_running": main_pipeline.is_running}
