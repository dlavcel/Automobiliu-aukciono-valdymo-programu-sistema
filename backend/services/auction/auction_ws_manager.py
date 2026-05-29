from collections import defaultdict
from uuid import UUID
from fastapi import WebSocket

class AuctionConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    def _room_key(self, auction_id: UUID | str) -> str:
        return str(auction_id)

    async def connect(self, auction_id: UUID | str, websocket: WebSocket) -> None:
        await websocket.accept()
        key = self._room_key(auction_id)
        self.active_connections[key].append(websocket)

    def disconnect(self, auction_id: UUID | str, websocket: WebSocket) -> None:
        key = self._room_key(auction_id)
        if key in self.active_connections and websocket in self.active_connections[key]:
            self.active_connections[key].remove(websocket)

        if key in self.active_connections and not self.active_connections[key]:
            del self.active_connections[key]

    async def broadcast(self, auction_id: UUID | str, message: dict) -> None:
        key = self._room_key(auction_id)
        connections = self.active_connections.get(key, [])
        print(f"[WS] connections in room {key}: {len(connections)}")
        print(f"[WS] broadcast to {key}: {message}")

        dead_connections = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(auction_id, connection)

auction_ws_manager = AuctionConnectionManager()