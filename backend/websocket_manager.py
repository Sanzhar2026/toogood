# backend/websocket_manager.py
from typing import Dict, Set
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.courier_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.supplier_connections: Dict[int, Set[WebSocket]] = {}
    
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
        elif user_type == "supplier":
            if user_id not in self.supplier_connections:
                self.supplier_connections[user_id] = set()
            self.supplier_connections[user_id].add(websocket)
        
        print(f"✅ {user_type} {user_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_type: str = None, user_id: int = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_type == "courier" and user_id and user_id in self.courier_connections:
            self.courier_connections[user_id].discard(websocket)
            if not self.courier_connections[user_id]:
                del self.courier_connections[user_id]
        elif user_type == "user" and user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        elif user_type == "supplier" and user_id and user_id in self.supplier_connections:
            self.supplier_connections[user_id].discard(websocket)
            if not self.supplier_connections[user_id]:
                del self.supplier_connections[user_id]
        else:
            # Fallback search
            for uid, conns in self.courier_connections.items():
                if websocket in conns:
                    conns.discard(websocket)
                    if not conns:
                        del self.courier_connections[uid]
                    break
            for uid, conns in self.user_connections.items():
                if websocket in conns:
                    conns.discard(websocket)
                    if not conns:
                        del self.user_connections[uid]
                    break
            for uid, conns in self.supplier_connections.items():
                if websocket in conns:
                    conns.discard(websocket)
                    if not conns:
                        del self.supplier_connections[uid]
                    break
    
    async def broadcast_to_all(self, message: dict):
        """Отправить всем подключенным клиентам"""
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except:
                disconnected.append(conn)
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_to_user(self, user_id: int, message: dict):
        """Отправить сообщение конкретному пользователю"""
        if user_id in self.user_connections:
            disconnected = []
            for conn in self.user_connections[user_id]:
                try:
                    await conn.send_json(message)
                except:
                    disconnected.append(conn)
            for conn in disconnected:
                self.disconnect(conn, "user", user_id)
    
    # ✅ НОВЫЙ МЕТОД ДЛЯ ОЧИСТКИ
    async def start_cleanup_task(self):
        """Фоновая очистка мертвых соединений"""
        while True:
            await asyncio.sleep(300)  # 5 минут
            
            dead_connections = []
            for conn in self.active_connections:
                try:
                    await asyncio.wait_for(conn.send_json({"type": "ping"}), timeout=1.0)
                except:
                    dead_connections.append(conn)
            
            for conn in dead_connections:
                self.disconnect(conn)
            
            if dead_connections:
                print(f"🧹 Очищено {len(dead_connections)} мертвых соединений")