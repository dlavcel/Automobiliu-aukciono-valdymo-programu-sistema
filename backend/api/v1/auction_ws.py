from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.auction.auction_ws_manager import auction_ws_manager

router = APIRouter(tags=["auction-ws"])

@router.websocket("/ws/auctions/{auction_id}")
async def auction_ws(websocket: WebSocket, auction_id: UUID):
    print(f"[WS] connect attempt {auction_id}")
    await auction_ws_manager.connect(auction_id, websocket)
    print(f"[WS] connected {auction_id}")

    try:
        await websocket.send_json({
            "event": "connected",
            "auction_id": str(auction_id),
        })

        while True:
            message = await websocket.receive_text()
            print(f"[WS] received from {auction_id}: {message}")
    except WebSocketDisconnect:
        print(f"[WS] disconnect {auction_id}")
        auction_ws_manager.disconnect(auction_id, websocket)
    except Exception as exc:
        print(f"[WS] error {auction_id}: {exc}")
        auction_ws_manager.disconnect(auction_id, websocket)