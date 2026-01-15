import json
import random
import socket
import subprocess
import uuid
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

# 允许跨域请求
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
        # 大屏连接集合
        self.screen_connections: Set[WebSocket] = set()
        # 手机端用户字典: {client_id: {"name": str, "socket": WebSocket}}
        self.connected_users: Dict[str, Dict] = {}
    
    async def connect_screen(self, websocket: WebSocket):
        """连接大屏客户端"""
        await websocket.accept()
        self.screen_connections.add(websocket)
        print(f"大屏已连接，当前大屏数量: {len(self.screen_connections)}")
    
    async def disconnect_screen(self, websocket: WebSocket):
        """断开大屏客户端"""
        if websocket in self.screen_connections:
            self.screen_connections.remove(websocket)
        print(f"大屏已断开，当前大屏数量: {len(self.screen_connections)}")
    
    async def connect_mobile(self, websocket: WebSocket, client_id: str, name: str):
        """连接手机客户端"""
        # websocket 已经在外部接受，这里只记录用户信息
        self.connected_users[client_id] = {
            "name": name,
            "socket": websocket
        }
        print(f"手机用户已连接: {name} (ID: {client_id})，当前用户数: {len(self.connected_users)}")
        # 向所有大屏广播更新
        await self.broadcast_user_update()
    
    async def disconnect_mobile(self, client_id: str):
        """断开手机客户端"""
        if client_id in self.connected_users:
            user_info = self.connected_users.pop(client_id)
            print(f"手机用户已断开: {user_info['name']} (ID: {client_id})，当前用户数: {len(self.connected_users)}")
            # 向所有大屏广播更新
            await self.broadcast_user_update()
    
    async def broadcast_user_update(self):
        """向所有大屏广播用户列表更新"""
        if not self.screen_connections:
            return
        
        users_list = [
            {"client_id": client_id, "name": info["name"]}
            for client_id, info in self.connected_users.items()
        ]
        
        message = {
            "type": "update_count",
            "count": len(self.connected_users),
            "users": users_list
        }
        
        # 向所有大屏发送
        disconnected = []
        for connection in self.screen_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"向大屏发送消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.screen_connections.discard(connection)
    
    async def draw_winner(self, prize: str = "一等奖"):
        """随机抽取中奖者"""
        if not self.connected_users:
            # 如果没有用户，通知所有大屏
            message = {
                "type": "draw_result",
                "winner": None,
                "prize": prize,
                "message": "暂无参与者"
            }
            disconnected = []
            for connection in self.screen_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"向大屏发送消息失败: {e}")
                    disconnected.append(connection)
            for connection in disconnected:
                self.screen_connections.discard(connection)
            return None
        
        # 随机选择一个用户
        client_id = random.choice(list(self.connected_users.keys()))
        winner_info = self.connected_users[client_id]
        winner_name = winner_info["name"]
        winner_socket = winner_info["socket"]
        
        # 向所有大屏广播中奖者
        message_to_screens = {
            "type": "draw_result",
            "winner": winner_name,
            "prize": prize,
            "client_id": client_id
        }
        
        disconnected = []
        for connection in self.screen_connections:
            try:
                await connection.send_json(message_to_screens)
            except Exception as e:
                print(f"向大屏发送消息失败: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.screen_connections.discard(connection)
        
        # 只向中奖者发送消息
        try:
            await winner_socket.send_json({
                "type": "you_won",
                "prize": prize
            })
            print(f"中奖者: {winner_name} (ID: {client_id})，奖品: {prize}")
        except Exception as e:
            print(f"向中奖者发送消息失败: {e}")
        
        # 中奖后从列表中移除（可选，如果需要一人只能中一次奖）
        # self.connected_users.pop(client_id, None)
        # await self.broadcast_user_update()
        
        return winner_name

# 创建连接管理器实例
manager = ConnectionManager()


def get_local_ip() -> str:
    """获取本机在局域网中的 IP 地址"""
    try:
        # 创建一个 UDP socket 来获取本地 IP
        # 不需要实际连接，只是用来获取本地网络接口信息
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 连接到一个外部地址（不需要实际连接成功）
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            # 如果上述方法失败，尝试使用 hostname
            ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()
        
        # 如果获取到的是 127.0.0.1，尝试其他方法
        if ip == '127.0.0.1' or ip.startswith('127.'):
            # 尝试通过遍历网络接口获取
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            
            # 如果还是 127.0.0.1，尝试获取实际网络接口
            if ip == '127.0.0.1':
                try:
                    # Windows 系统
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                    for line in result.stdout.split('\n'):
                        if 'IPv4' in line or 'IP Address' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                potential_ip = parts[-1].strip()
                                if potential_ip.startswith('192.168.') or potential_ip.startswith('10.') or potential_ip.startswith('172.'):
                                    ip = potential_ip
                                    break
                except:
                    pass
        
        return ip
    except Exception as e:
        print(f"获取 IP 地址失败: {e}")
        return "127.0.0.1"


@app.get("/api/get-ip")
async def get_ip():
    """获取本机 IP 地址的 API"""
    ip = get_local_ip()
    port = 8000  # 默认端口，可以根据实际情况修改
    return JSONResponse({
        "ip": ip,
        "port": port,
        "url": f"ws://{ip}:{port}/ws"
    })


@app.websocket("/ws/screen")
async def websocket_screen(websocket: WebSocket):
    """大屏端的 WebSocket 连接"""
    await manager.connect_screen(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "draw":
                    # 处理抽奖请求
                    prize = message.get("prize", "一等奖")
                    await manager.draw_winner(prize)
                elif message_type == "get_users":
                    # 请求当前用户列表
                    await manager.broadcast_user_update()
                else:
                    print(f"未知的大屏消息类型: {message_type}")
            
            except json.JSONDecodeError:
                print(f"收到无效的 JSON 消息: {data}")
            except Exception as e:
                print(f"处理大屏消息时出错: {e}")
    
    except WebSocketDisconnect:
        await manager.disconnect_screen(websocket)
    except Exception as e:
        print(f"大屏 WebSocket 连接错误: {e}")
        await manager.disconnect_screen(websocket)


@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    """手机端的 WebSocket 连接"""
    client_id = str(uuid.uuid4())  # 连接时立即生成 client_id
    await websocket.accept()  # 先接受连接
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "login":
                    # 手机端登录
                    name = message.get("name", "匿名用户")
                    await manager.connect_mobile(websocket, client_id, name)
                else:
                    print(f"未知的手机消息类型: {message_type}")
            
            except json.JSONDecodeError:
                print(f"收到无效的 JSON 消息: {data}")
            except Exception as e:
                print(f"处理手机消息时出错: {e}")
    
    except WebSocketDisconnect:
        if client_id in manager.connected_users:
            await manager.disconnect_mobile(client_id)
    except Exception as e:
        print(f"手机 WebSocket 连接错误: {e}")
        if client_id in manager.connected_users:
            await manager.disconnect_mobile(client_id)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "抽奖系统后端服务", "status": "running"}


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return JSONResponse({
        "screen_count": len(manager.screen_connections),
        "mobile_count": len(manager.connected_users),
        "users": [
            {"client_id": client_id, "name": info["name"]}
            for client_id, info in manager.connected_users.items()
        ]
    })


if __name__ == "__main__":
    # 获取本机 IP 并打印
    ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"抽奖系统后端服务启动中...")
    print(f"本机 IP 地址: {ip}")
    print(f"WebSocket 大屏连接: ws://{ip}:8000/ws/screen")
    print(f"WebSocket 手机连接: ws://{ip}:8000/ws/mobile")
    print(f"API 获取 IP: http://{ip}:8000/api/get-ip")
    print(f"{'='*50}\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

