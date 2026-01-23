from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
import socket
import json
from typing import Dict, List

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.screen_connections: List[WebSocket] = []
        self.mobile_connections: Dict[str, Dict] = {}  # {client_id: {"name": "...", "socket": websocket}}

    async def connect_screen(self, websocket: WebSocket):
        await websocket.accept()
        self.screen_connections.append(websocket)
        print(f"大屏连接成功，当前大屏数: {len(self.screen_connections)}")

    async def disconnect_screen(self, websocket: WebSocket):
        if websocket in self.screen_connections:
            self.screen_connections.remove(websocket)
        print(f"大屏断开连接，当前大屏数: {len(self.screen_connections)}")

    async def connect_mobile(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.mobile_connections[client_id] = {"name": "", "socket": websocket}
        print(f"手机连接成功，客户端ID: {client_id}，当前手机数: {len(self.mobile_connections)}")
        await self.broadcast_user_count()

    async def disconnect_mobile(self, client_id: str):
        if client_id in self.mobile_connections:
            del self.mobile_connections[client_id]
        print(f"手机断开连接，客户端ID: {client_id}，当前手机数: {len(self.mobile_connections)}")
        await self.broadcast_user_count()

    async def login_mobile(self, client_id: str, name: str):
        if client_id in self.mobile_connections:
            self.mobile_connections[client_id]["name"] = name
            print(f"用户登录: {name} (ID: {client_id})")
            await self.broadcast_user_count()

    async def broadcast_user_count(self):
        """向所有大屏广播用户数量和用户列表"""
        count = len(self.mobile_connections)
        users = [
            {"name": info["name"], "id": client_id}
            for client_id, info in self.mobile_connections.items()
            if info["name"]  # 只包含已登录的用户
        ]
        
        message = {
            "type": "update_count",
            "count": count,
            "users": users
        }
        
        # 向所有大屏发送
        disconnected = []
        for connection in self.screen_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"向大屏发送消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            await self.disconnect_screen(conn)

    async def draw_winner(self):
        """从已登录的用户中随机抽取一个"""
        logged_in_users = [
            (client_id, info["name"])
            for client_id, info in self.mobile_connections.items()
            if info["name"]
        ]
        
        if not logged_in_users:
            return None
        
        winner_id, winner_name = random.choice(logged_in_users)
        return winner_id, winner_name

    async def broadcast_winner(self, winner_name: str):
        """向大屏广播中奖者"""
        message = {
            "type": "winner",
            "name": winner_name
        }
        
        disconnected = []
        for connection in self.screen_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"向大屏发送中奖消息失败: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            await self.disconnect_screen(conn)

    async def notify_winner_mobile(self, client_id: str, prize: str = "一等奖"):
        """向中奖的手机发送通知"""
        if client_id in self.mobile_connections:
            message = {
                "type": "you_won",
                "prize": prize
            }
            try:
                await self.mobile_connections[client_id]["socket"].send_text(json.dumps(message))
            except Exception as e:
                print(f"向手机发送中奖消息失败: {e}")

manager = ConnectionManager()

# 获取本机 IP 地址
def get_local_ip():
    """获取本机在局域网中的 IP 地址"""
    try:
        # 创建一个 UDP socket（不会实际发送数据）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 连接到外部地址
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # 备用方法：获取主机名对应的 IP
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "127.0.0.1"

# API 路由
@app.get("/api/get-ip")
async def get_ip():
    """获取本机 IP 地址"""
    ip = get_local_ip()
    return {"ip": ip}

# WebSocket 路由
@app.websocket("/ws/screen")
async def websocket_screen(websocket: WebSocket):
    """大屏 WebSocket 连接"""
    await manager.connect_screen(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "draw":
                # 抽奖请求
                winner_id, winner_name = await manager.draw_winner()
                if winner_id and winner_name:
                    # 向大屏广播中奖者
                    await manager.broadcast_winner(winner_name)
                    # 向中奖的手机发送通知
                    await manager.notify_winner_mobile(winner_id, "一等奖")
                else:
                    # 没有用户时，向大屏发送错误消息
                    error_message = {
                        "type": "error",
                        "message": "当前没有已登录的用户"
                    }
                    await websocket.send_text(json.dumps(error_message))
    except WebSocketDisconnect:
        await manager.disconnect_screen(websocket)

@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    """手机 WebSocket 连接"""
    import uuid
    client_id = str(uuid.uuid4())
    
    await manager.connect_mobile(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "login":
                name = message.get("name", "").strip()
                if name:
                    await manager.login_mobile(client_id, name)
                    # 向手机发送登录成功消息
                    success_message = {
                        "type": "login_success",
                        "message": "登录成功，等待抽奖开始"
                    }
                    await websocket.send_text(json.dumps(success_message))
    except WebSocketDisconnect:
        await manager.disconnect_mobile(client_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
