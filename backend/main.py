from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import random
import socket
import json
import pandas as pd
from datetime import datetime
import os

# 导入数据库和后台管理 API
from database import init_db, get_db
from admin_api import router as admin_router
from shake_api import router as shake_router

app = FastAPI(title="新年抽奖系统 API", version="1.0.0")

# 初始化数据库
init_db()

# 挂载静态文件目录
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册后台管理路由
app.include_router(admin_router)

# 注册摇一摇游戏路由
app.include_router(shake_router)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 【核心功能重构】全局去重集合 ==========
winners_set = set()  # 记录所有已中奖的 user_id，防止重复中奖

# ========== 【核心功能重构】Excel 持久化 ==========
EXCEL_FILE = "lottery_results.xlsx"

def save_to_excel(winners: List[Dict], prize_name: str):
    """将中奖信息追加写入 Excel 文件"""
    try:
        # 准备数据
        data = []
        for winner in winners:
            data.append({
                "工号": winner.get("id", ""),
                "姓名": winner.get("name", ""),
                "奖项": prize_name,
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # 如果文件存在，追加数据；否则创建新文件
        if os.path.exists(EXCEL_FILE):
            df_existing = pd.read_excel(EXCEL_FILE)
            df_new = pd.DataFrame(data)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(EXCEL_FILE, index=False)
        else:
            df_new = pd.DataFrame(data)
            df_new.to_excel(EXCEL_FILE, index=False)
        
        print(f"已保存 {len(winners)} 条中奖记录到 {EXCEL_FILE}")
    except Exception as e:
        print(f"保存 Excel 失败: {e}")

# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.screen_connections: List[WebSocket] = []
        self.mobile_connections: Dict[str, Dict] = {}  # {client_id: {"name": "", "socket": websocket, "id": ""}}
        self.logged_in_users: Dict[str, Dict] = {}  # {client_id: {"name": "...", "socket": websocket, "id": "..."}}

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
        self.mobile_connections[client_id] = {"name": "", "socket": websocket, "id": ""}
        print(f"手机连接成功，客户端ID: {client_id}，当前连接数: {len(self.mobile_connections)}，已登录数: {len(self.logged_in_users)}")

    async def disconnect_mobile(self, client_id: str):
        if client_id in self.mobile_connections:
            del self.mobile_connections[client_id]
        if client_id in self.logged_in_users:
            del self.logged_in_users[client_id]
        print(f"手机断开连接，客户端ID: {client_id}，当前连接数: {len(self.mobile_connections)}，已登录数: {len(self.logged_in_users)}")
        await self.broadcast_user_count()

    async def login_mobile(self, client_id: str, name: str, user_id: str = ""):
        if client_id in self.mobile_connections:
            socket = self.mobile_connections[client_id]["socket"]
            self.mobile_connections[client_id]["name"] = name
            self.mobile_connections[client_id]["id"] = user_id
            self.logged_in_users[client_id] = {
                "name": name,
                "socket": socket,
                "id": user_id
            }
            print(f"用户登录成功: {name} (工号: {user_id}, 连接ID: {client_id})，当前已登录数: {len(self.logged_in_users)}")
            await self.broadcast_user_count()
            return True
        return False

    async def broadcast_user_count(self):
        """向所有大屏广播用户数量和用户列表"""
        count = len(self.logged_in_users)
        users = [
            {"name": info["name"], "id": info.get("id", ""), "employeeId": info.get("id", "")}
            for client_id, info in self.logged_in_users.items()
        ]
        
        message = {
            "type": "update_count",
            "count": count,
            "users": users
        }
        
        disconnected = []
        for connection in self.screen_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"向大屏发送消息失败: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            await self.disconnect_screen(conn)

    async def broadcast_winners(self, winners: List[Dict], prize_name: str):
        """向大屏广播中奖者列表"""
        message = {
            "type": "draw_result",
            "winners": winners,
            "prize": prize_name
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

    async def broadcast_screen_control(self, message: Dict):
        """向大屏广播控制指令（后台管理用）"""
        disconnected = []
        for connection in self.screen_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"向大屏发送控制指令失败: {e}")
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

    async def broadcast_shake_message(self, message: Dict):
        """向所有摇一摇游戏连接广播消息"""
        # 这里需要维护一个摇一摇游戏的 WebSocket 连接列表
        # 暂时使用 mobile_connections（可以后续分离）
        disconnected = []
        for client_id, info in self.mobile_connections.items():
            try:
                await info["socket"].send_text(json.dumps(message))
            except Exception as e:
                print(f"向摇一摇客户端发送消息失败: {e}")
                disconnected.append(client_id)
        
        for client_id in disconnected:
            await self.disconnect_mobile(client_id)

manager = ConnectionManager()

# ========== 【核心功能重构】抽奖请求模型 ==========
class DrawRequest(BaseModel):
    count: int  # 本次抽取数量
    prize_name: str  # 奖项名称

# 获取本机 IP 地址
def get_local_ip():
    """获取本机在局域网中的 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
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

# ========== 【核心功能重构】批量抽奖接口 ==========
@app.post("/api/draw")
async def draw_winners(request: DrawRequest):
    """
    批量抽奖接口
    入参：count (本次抽取数量), prize_name (奖项名称)
    逻辑：去重、过滤、随机抽取、记录、持久化
    """
    global winners_set
    
    # 1. 获取所有在线用户
    if not manager.logged_in_users:
        raise HTTPException(status_code=400, detail="当前没有已登录的用户")
    
    # 2. 过滤：剔除已中奖用户，生成候选池
    candidates = []
    for client_id, info in manager.logged_in_users.items():
        user_id = info.get("id", "")
        # 如果用户有工号，用工号去重；否则用client_id
        unique_id = user_id if user_id else client_id
        if unique_id not in winners_set:
            candidates.append({
                "client_id": client_id,
                "name": info["name"],
                "id": user_id,
                "unique_id": unique_id
            })
    
    # 3. 校验：候选池数量是否足够
    if len(candidates) < request.count:
        # 如果候选池不足，只抽取剩余人数
        actual_count = len(candidates)
        if actual_count == 0:
            raise HTTPException(status_code=400, detail="所有用户都已中奖，没有可抽取的候选者")
        print(f"警告：候选池只有 {actual_count} 人，少于请求的 {request.count} 人，将只抽取 {actual_count} 人")
    else:
        actual_count = request.count
    
    # 4. 随机抽取
    selected = random.sample(candidates, actual_count)
    
    # 5. 记录到去重集合
    winners = []
    for item in selected:
        winners_set.add(item["unique_id"])
        winners.append({
            "name": item["name"],
            "id": item["id"],
            "employeeId": item["id"]
        })
    
    # 6. 持久化到 Excel
    save_to_excel(winners, request.prize_name)
    
    # 7. 向大屏广播中奖者
    await manager.broadcast_winners(winners, request.prize_name)
    
    # 8. 向中奖的手机发送通知
    for item in selected:
        await manager.notify_winner_mobile(item["client_id"], request.prize_name)
    
    return {
        "success": True,
        "winners": winners,
        "prize": request.prize_name,
        "count": len(winners)
    }

# ========== 【核心功能重构】重置抽奖接口（可选，用于测试） ==========
@app.post("/api/reset")
async def reset_lottery():
    """重置抽奖（清空已中奖记录）"""
    global winners_set
    winners_set.clear()
    return {"success": True, "message": "抽奖已重置"}

# ========== 【导出中奖名单】 ==========
@app.get("/api/export_winners")
async def export_winners():
    """
    导出中奖名单 Excel 文件
    - 文件由 save_to_excel 写入 EXCEL_FILE
    - 如果文件不存在，返回 404
    """
    file_path = os.path.abspath(EXCEL_FILE)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"导出失败：文件不存在（{EXCEL_FILE}），请先完成一次抽奖")

    # 让浏览器下载
    filename = f"中奖名单_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )

# WebSocket 路由
@app.websocket("/ws/screen")
async def websocket_screen(websocket: WebSocket):
    """大屏 WebSocket 连接"""
    await manager.connect_screen(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_users":
                # 立即返回用户列表
                await manager.broadcast_user_count()
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
            
            if message.get("type") == "ping":
                try:
                    await websocket.send_text(json.dumps({"type": "pong"}))
                except Exception as e:
                    print(f"发送心跳响应失败: {e}")
                continue
            
            if message.get("type") == "login":
                name = message.get("name", "").strip()
                user_id = message.get("id", "").strip()
                if name:
                    success = await manager.login_mobile(client_id, name, user_id)
                    if success:
                        login_ok_message = {
                            "type": "login_ok"
                        }
                        await websocket.send_text(json.dumps(login_ok_message))
                        print(f"已向客户端 {client_id} 发送 login_ok")
                    else:
                        error_message = {
                            "type": "login_error",
                            "message": "登录失败，请重试"
                        }
                        await websocket.send_text(json.dumps(error_message))
                else:
                    error_message = {
                        "type": "login_error",
                        "message": "姓名不能为空"
                    }
                    await websocket.send_text(json.dumps(error_message))
    except WebSocketDisconnect:
        await manager.disconnect_mobile(client_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
