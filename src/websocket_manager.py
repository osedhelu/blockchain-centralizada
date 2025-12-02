import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class WebSocketManager:
    """
    Administra conexiones WebSocket por dirección de wallet.
    Las direcciones se almacenan en minúsculas.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, address: str, websocket: WebSocket) -> None:
        address = address.lower()
        await websocket.accept()
        async with self._lock:
            if address not in self._connections:
                self._connections[address] = set()
            self._connections[address].add(websocket)

    async def disconnect(self, address: str, websocket: WebSocket) -> None:
        address = address.lower()
        async with self._lock:
            if address in self._connections:
                self._connections[address].discard(websocket)
                if not self._connections[address]:
                    del self._connections[address]

    async def send_personal_message(self, address: str, message: dict) -> None:
        """
        Envía un mensaje a todas las conexiones asociadas a una dirección.
        """
        address = address.lower()
        async with self._lock:
            connections = list(self._connections.get(address, set()))
        if not connections:
            return

        data = message
        for connection in connections:
            try:
                await connection.send_json(data)
            except Exception:
                # Si falla, intentamos desconectarlo silenciosamente
                await self.disconnect(address, connection)


ws_manager = WebSocketManager()



