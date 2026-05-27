class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.courier_connections: Dict[int, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self._cleanup_interval = 300  # 5 минут
    
    async def start_cleanup_task(self):
        """Фоновая очистка мертвых соединений"""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            await self.cleanup_dead_connections()
    
    async def cleanup_dead_connections(self):
        """Очистка неактивных соединений"""
        dead_connections = []
        for conn in self.active_connections:
            try:
                # Проверяем, живо ли соединение
                await asyncio.wait_for(conn.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                # Соединение живое, но нет данных
                pass
            except Exception:
                # Соединение мертвое
                dead_connections.append(conn)
        
        for conn in dead_connections:
            self.disconnect(conn)
        
        if dead_connections:
            print(f"🧹 Очищено {len(dead_connections)} мертвых соединений")