# backend/websocket_manager.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
from typing import Dict, List, Set
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.courier_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.supplier_connections: Dict[int, Set[WebSocket]] = {}
        self.supplier_connections_str: Dict[str, List[WebSocket]] = {}
    
    # ============ НОВЫЕ МЕТОДЫ (с поддержкой типов) ============
    
    async def connect(self, websocket: WebSocket, user_type: str, user_id: int):
        """Подключение с указанием типа пользователя"""
        # await websocket.accept()
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
    
    # ============ СТАРЫЙ МЕТОД connect (для обратной совместимости) ============
    
    async def connect_legacy(self, websocket: WebSocket):
        """Старый метод подключения (без указания типа)"""
        # await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ WebSocket connected. Total: {len(self.active_connections)}")
    
    # ============ НОВЫЙ disconnect ============
    
    def disconnect(self, websocket: WebSocket, user_type: str = None, user_id: int = None):
        """Отключение с указанием типа пользователя"""
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
            self._remove_from_all_dicts(websocket)
        
        # Также удаляем из старого словаря supplier_connections_str
        for supplier_id in list(self.supplier_connections_str.keys()):
            if websocket in self.supplier_connections_str[supplier_id]:
                self.supplier_connections_str[supplier_id].remove(websocket)
                if not self.supplier_connections_str[supplier_id]:
                    del self.supplier_connections_str[supplier_id]
        
        print(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    def _remove_from_all_dicts(self, websocket: WebSocket):
        """Поиск и удаление websocket из всех словарей"""
        for uid, conns in self.courier_connections.items():
            if websocket in conns:
                conns.discard(websocket)
                if not conns:
                    del self.courier_connections[uid]
                return
        for uid, conns in self.user_connections.items():
            if websocket in conns:
                conns.discard(websocket)
                if not conns:
                    del self.user_connections[uid]
                return
        for uid, conns in self.supplier_connections.items():
            if websocket in conns:
                conns.discard(websocket)
                if not conns:
                    del self.supplier_connections[uid]
                return
    
    # ============ СТАРЫЙ МЕТОД disconnect (для обратной совместимости) ============
    
    def disconnect_legacy(self, websocket: WebSocket):
        """Старый метод отключения"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        for supplier_id in list(self.supplier_connections_str.keys()):
            if websocket in self.supplier_connections_str[supplier_id]:
                self.supplier_connections_str[supplier_id].remove(websocket)
                if not self.supplier_connections_str[supplier_id]:
                    del self.supplier_connections_str[supplier_id]
        
        print(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    # ============ НОВЫЕ МЕТОДЫ ============
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Отправить личное сообщение"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Отправить сообщение всем подписчикам канала"""
        disconnected = []
        
        if channel == "all":
            clients = list(self.active_connections)
        elif channel.startswith("supplier_"):
            supplier_id = channel.replace("supplier_", "")
            clients = self.supplier_connections_str.get(supplier_id, []).copy()
        else:
            clients = list(self.active_connections)
        
        for connection in clients:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect_legacy(connection)
    
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
    
    async def subscribe_supplier(self, websocket: WebSocket, supplier_id: str):
        """Подписать поставщика на его канал"""
        if supplier_id not in self.supplier_connections_str:
            self.supplier_connections_str[supplier_id] = []
        if websocket not in self.supplier_connections_str[supplier_id]:
            self.supplier_connections_str[supplier_id].append(websocket)
            print(f"📡 Supplier {supplier_id} subscribed")
    
    # ✅ РАСКОММЕНТИРОВАНО - теперь работает!
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