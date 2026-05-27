# backend/websocket_manager.py
from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.courier_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_type: str, user_id: int):
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if user_type == "courier":
            if user_id not in self.courier_connections:
                self.courier_connections[user_id] = set()
            self.courier_connections[user_id].add(websocket)
        elif user_type == "user":
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        print(f"✅ {user_type} {user_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_type: str = None, user_id: int = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_to_all(self, message: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except:
                pass

manager = ConnectionManager()