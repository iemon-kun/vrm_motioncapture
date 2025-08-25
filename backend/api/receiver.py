from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.ps_receiver import ps_receiver_instance

router = APIRouter(
    prefix="/ws",
    tags=["Receivers"],
)

@router.websocket("/ps_receiver")
async def websocket_perfect_sync_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to receive Perfect Sync data from apps like iFacialMocap.
    """
    await websocket.accept()
    print("Perfect Sync client connected.")
    try:
        while True:
            # iFacialMocap sends data as bytes
            data = await websocket.receive_bytes()
            ps_receiver_instance.process_data(data)
            # For debugging purposes, one might echo back the latest state
            # latest_shapes = ps_receiver_instance.get_latest_blendshapes()
            # await websocket.send_json(latest_shapes)
    except WebSocketDisconnect:
        print("Perfect Sync client disconnected.")
    except Exception as e:
        print(f"An error occurred in the Perfect Sync websocket: {e}")
        await websocket.close(code=1011)
