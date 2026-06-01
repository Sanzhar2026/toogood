# backend/websocket_manager.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
from typing import Dict, List, Set
from fastapi import WebSocket
import asyncio
import gc

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.general_connections: List[WebSocket] = []  # ✅ ДОБАВЛЕНО
        self.courier_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.supplier_connections: Dict[int, Set[WebSocket]] = {}
        self.supplier_connections_str: Dict[str, List[WebSocket]] = {}
    
    # ============ МЕТОДЫ ДЛЯ LEGACY КЛИЕНТОВ ============
    
    async def connect_legacy(self, websocket: WebSocket):
        """Подключение клиента без авторизации"""
        self.general_connections.append(websocket)
        print(f"✅ Legacy client connected. Total: {len(self.general_connections)}")
        
        try:
            await websocket.send_json({
                "type": "connected",
                "message": "Connected to WebSocket"
            })
        except:
            pass
    
    async def disconnect_legacy(self, websocket: WebSocket):
        """Отключение клиента без авторизации"""
        if websocket in self.general_connections:
            self.general_connections.remove(websocket)
            print(f"🔌 Legacy client disconnected. Total: {len(self.general_connections)}")
            gc.collect()
    
    # ============ МЕТОДЫ ДЛЯ АВТОРИЗОВАННЫХ КЛИЕНТОВ ============
    
    async def connect(self, websocket: WebSocket, user_type: str, user_id: int):
        """Подключение с указанием типа пользователя"""
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
        
        try:
            await websocket.send_json({
                "type": "connected",
                "user_type": user_type,
                "user_id": user_id
            })
        except:
            pass
    
    async def disconnect(self, websocket: WebSocket, user_type: str = None, user_id: int = None):
        """Отключение авторизованного пользователя"""
        # Удаляем из active_connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Если знаем тип и ID - удаляем из соответствующего словаря
        if user_type and user_id:
            if user_type == "courier" and user_id in self.courier_connections:
                self.courier_connections[user_id].discard(websocket)
                if not self.courier_connections[user_id]:
                    del self.courier_connections[user_id]
            elif user_type == "user" and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            elif user_type == "supplier" and user_id in self.supplier_connections:
                self.supplier_connections[user_id].discard(websocket)
                if not self.supplier_connections[user_id]:
                    del self.supplier_connections[user_id]
        else:
            # Если не знаем тип - ищем во всех словарях
            self._remove_from_all_dicts(websocket)
        
        print(f"🔌 User disconnected. Total: {len(self.active_connections)}")
        gc.collect()
    
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
    
    # ============ МЕТОДЫ ДЛЯ ОТПРАВКИ СООБЩЕНИЙ ============
    
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
            await self.disconnect_legacy(connection)
    
    async def broadcast_to_all(self, message: dict):
        """Отправить всем подключенным клиентам"""
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except:
                disconnected.append(conn)
        for conn in disconnected:
            await self.disconnect(conn)
    
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
                await self.disconnect(conn, "user", user_id)
    
    async def subscribe_supplier(self, websocket: WebSocket, supplier_id: str):
        """Подписать поставщика на его канал"""
        if supplier_id not in self.supplier_connections_str:
            self.supplier_connections_str[supplier_id] = []
        if websocket not in self.supplier_connections_str[supplier_id]:
            self.supplier_connections_str[supplier_id].append(websocket)
            print(f"📡 Supplier {supplier_id} subscribed")
    
    # ============ ФОНОВЫЕ ЗАДАЧИ ============
    
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
                await self.disconnect(conn)
            
            if dead_connections:
                print(f"🧹 Очищено {len(dead_connections)} мертвых соединений")
            gc.collect()
    
    async def cleanup_stale_connections(self):
        """Очистка мертвых соединений"""
        alive = []
        for ws in self.general_connections:
            try:
                await ws.send_json({"type": "ping"})
                alive.append(ws)
            except:
                pass
        
        self.general_connections = alive
        print(f"🧹 Cleaned up connections. Total: {len(self.general_connections)}")
        gc.collect()

# Создаем глобальный экземпляр
manager = ConnectionManager()