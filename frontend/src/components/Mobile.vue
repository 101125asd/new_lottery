<template>
  <div class="mobile-container">
    <!-- 状态1: 未登录 -->
    <div v-if="status === 'login'" class="login-state">
      <div class="login-content">
        <h1 class="app-title">新年抽奖</h1>
        <div v-if="isIOSDevice" class="ios-hint">
          <p>📱 iOS 设备提示：</p>
          <p>请确保手机和电脑在同一 WiFi 网络</p>
        </div>
        <div class="input-wrapper">
          <input
            v-model="userName"
            type="text"
            placeholder="请输入您的姓名"
            class="name-input"
            @keyup.enter="joinLottery"
            maxlength="20"
          />
          <input
            v-model="ID"
             type="text"
            placeholder="请输入您的工号"
            class="id-input"
            @keyup.enter="joinLottery"
            maxlength="20"
          />

        </div>
        <button @click="joinLottery" class="join-button" :disabled="!userName.trim()">
          加入战场
        </button>
      </div>
    </div>

    <!-- 状态2: 等待中 -->
    <div v-if="status === 'waiting'" class="waiting-state">
      <div class="waiting-content">
        <div class="waiting-icon">🎁</div>
        <h2 class="waiting-text">已连接，等待大奖降临...</h2>
        <div class="breathing-dot"></div>
      </div>
    </div>

    <!-- 状态3: 中奖了 -->
    <div v-if="status === 'won'" class="won-state">
      <div class="won-overlay">
        <div class="won-content">
          <div class="won-icon">🎉</div>
          <h1 class="won-title">恭喜你中奖了！</h1>
          <div class="won-prize">{{ prize }}</div>
          <div class="won-user-info">
            <div class="won-user-name">{{ userName }}</div>
            <div v-if="ID" class="won-user-id">工号：{{ ID }}</div>
          </div>
          <button @click="resetState" class="back-button">返回</button>
        </div>
      </div>
    </div>

    <!-- 状态4: 连接错误 -->
    <div v-if="status === 'error'" class="error-state">
      <div class="error-content">
        <div class="error-icon">⚠️</div>
        <h2 class="error-title">连接失败</h2>
        <p class="error-message">{{ errorMessage }}</p>
        <button @click="retryConnection" class="retry-button">重试连接</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// ========== 【修复1】添加 ID ref，修复 v-model="ID" 未定义的问题 ==========
const status = ref('login') // 'login' | 'waiting' | 'won' | 'error'
const userName = ref('')
const ID = ref('') // 【修复】添加 ID ref
const prize = ref('')
const errorMessage = ref('')
const isIOSDevice = ref(false)
let ws = null
let reconnectAttempts = 0
const maxReconnectAttempts = 5
let wsConnected = false
// ========== 【为修复 iOS Safari 问题新增】心跳定时器 ==========
let heartbeatInterval = null
const HEARTBEAT_INTERVAL = 20000 // 20秒心跳

// ========== 【为修复 iOS Safari 问题新增】WebSocket 地址生成 ==========
// 禁止使用 localhost 或 127.0.0.1，必须基于 location.hostname 动态生成
// 根据当前页面协议自动选择 ws / wss，端口固定为 8000
const getWebSocketUrl = (path) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const hostname = window.location.hostname
  // 确保不使用 localhost 或 127.0.0.1
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    console.warn('警告：当前 hostname 为 localhost，手机端可能无法连接。请使用局域网 IP 访问。')
  }
  return `${protocol}//${hostname}:8000${path}`
}

// 检测是否为 iOS 设备
const isIOS = () => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
}

// 连接 WebSocket
const connectWebSocket = () => {
  // 如果已经连接，直接返回
  if (ws && ws.readyState === WebSocket.OPEN) {
    console.log('WebSocket 已连接，跳过')
    return
  }
  
  // 如果正在连接，等待
  if (ws && ws.readyState === WebSocket.CONNECTING) {
    console.log('WebSocket 正在连接中，等待...')
    return
  }
  
  try {
    // 【修复】使用本地实现的 getWebSocketUrl，基于 location.hostname
    const wsUrl = getWebSocketUrl('/ws/mobile')
    console.log('尝试连接 WebSocket:', wsUrl)
    console.log('当前设备:', isIOSDevice.value ? 'iOS' : '其他')
    console.log('用户代理:', navigator.userAgent)
    
    // 关闭旧连接
    if (ws) {
      try {
        ws.close()
      } catch (e) {
        console.log('关闭旧连接时出错:', e)
      }
    }
    
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('手机 WebSocket 连接成功')
      wsConnected = true
      reconnectAttempts = 0
      errorMessage.value = ''
      // 如果当前是错误状态，切换回登录状态
      if (status.value === 'error') {
        status.value = 'login'
      }
      // ========== 【为修复 iOS Safari 问题新增】启动心跳机制 ==========
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleMessage(message)
      } catch (e) {
        console.error('解析消息失败:', e)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      // 不立即显示错误，等待 onclose 事件
    }

    ws.onclose = (event) => {
      console.log('WebSocket 连接关闭', event.code, event.reason)
      wsConnected = false
      // ========== 【为修复 iOS Safari 问题新增】停止心跳 ==========
      stopHeartbeat()
      
      // 如果连接失败且不是正常关闭，且当前不是中奖状态
      if (event.code !== 1000 && status.value !== 'won') {
        reconnectAttempts++
        
        if (reconnectAttempts <= maxReconnectAttempts) {
          // 显示错误信息
          status.value = 'error'
          const iosHint = isIOS() ? '\n提示：iOS 设备请确保网络连接正常，并允许 Safari 访问网络。' : ''
          errorMessage.value = `连接失败 (${reconnectAttempts}/${maxReconnectAttempts})，正在重试...${iosHint}`
          
          // 自动重连
          setTimeout(() => {
            if (status.value !== 'won' && !wsConnected) {
              connectWebSocket()
            }
          }, 3000)
        } else {
          // 超过最大重试次数
          status.value = 'error'
          const iosHint = isIOS() 
            ? '\n\niOS 设备提示：\n1. 确保手机和电脑在同一 WiFi 网络\n2. 检查 Safari 是否允许访问网络\n3. 尝试刷新页面重试' 
            : '\n\n请检查：\n1. 网络连接是否正常\n2. 后端服务是否运行\n3. 防火墙设置'
          errorMessage.value = `无法连接到服务器，请检查网络连接或联系管理员${iosHint}`
        }
      } else if (status.value === 'waiting') {
        // 如果是在等待状态时断开，尝试重连
        reconnectAttempts++
        if (reconnectAttempts <= maxReconnectAttempts) {
          setTimeout(() => {
            if (status.value === 'waiting' && !wsConnected) {
              connectWebSocket()
            }
          }, 3000)
        }
      }
    }
  } catch (error) {
    console.error('创建 WebSocket 连接失败:', error)
    status.value = 'error'
    errorMessage.value = '无法创建连接，请检查网络设置'
  }
}

// ========== 【为修复 iOS Safari 问题新增】心跳机制 ==========
const startHeartbeat = () => {
  stopHeartbeat() // 先清除旧的定时器
  heartbeatInterval = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify({ type: 'ping' }))
        console.log('发送心跳 ping')
      } catch (e) {
        console.error('发送心跳失败:', e)
      }
    } else {
      stopHeartbeat()
    }
  }, HEARTBEAT_INTERVAL)
}

const stopHeartbeat = () => {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
}

// 处理 WebSocket 消息
const handleMessage = (message) => {
  // ========== 【为修复 iOS Safari 问题新增】处理登录确认 ==========
  if (message.type === 'login_ok') {
    // 只有收到 login_ok 后才进入 waiting 状态
    // 这确保 iOS 设备即使连接慢也能正确加入抽奖池
    console.log('收到登录确认，进入等待状态')
    status.value = 'waiting'
    return
  }
  
  if (message.type === 'you_won') {
    prize.value = message.prize || '一等奖'
    status.value = 'won'
    // 震动手机
    vibrate()
  }
  
  // ========== 【为修复 iOS Safari 问题新增】处理心跳响应（可选） ==========
  if (message.type === 'pong') {
    console.log('收到心跳响应 pong')
  }
}

// ========== 【为修复 iOS Safari 问题修改】joinLottery：显式登录确认机制 ==========
// 加入抽奖 - 关键修复：必须等待 login_ok 后才进入 waiting 状态
const joinLottery = async () => {
  if (!userName.value.trim()) {
    return
  }

  // ========== 【为修复 iOS Safari 问题修改】所有设备都在用户点击时才连接 WebSocket ==========
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    // 先连接 WebSocket
    connectWebSocket()
    
    // 严格等待连接成功后再发送，确保 readyState === OPEN
    let attempts = 0
    const maxAttempts = 50 // 5秒超时
    
    const checkConnection = setInterval(() => {
      attempts++
      // 严格检查 readyState === OPEN
      if (ws && ws.readyState === WebSocket.OPEN) {
        clearInterval(checkConnection)
        // ========== 【为修复 iOS Safari 问题修改】发送 login 消息，但不立即切换状态 ==========
        // 状态切换将在收到 login_ok 后在 handleMessage 中处理
        ws.send(JSON.stringify({
          type: 'login',
          name: userName.value.trim(),
          id: ID.value.trim() || '' // 发送 ID，如果没有则发送空字符串
        }))
        // 注意：这里不设置 status.value = 'waiting'，等待 login_ok
      } else if (attempts >= maxAttempts) {
        clearInterval(checkConnection)
        status.value = 'error'
        errorMessage.value = '连接超时，请点击"重试连接"按钮'
      }
    }, 100)
  } else {
    // 已连接且状态为 OPEN，直接发送（包含 ID）
    if (ws.readyState === WebSocket.OPEN) {
      // ========== 【为修复 iOS Safari 问题修改】发送 login，等待 login_ok ==========
      ws.send(JSON.stringify({
        type: 'login',
        name: userName.value.trim(),
        id: ID.value.trim() || '' // 发送 ID，如果没有则发送空字符串
      }))
      // 注意：这里不设置 status.value = 'waiting'，等待 login_ok
    } else {
      // 如果状态不是 OPEN，重新连接
      connectWebSocket()
      joinLottery() // 递归调用，等待连接后发送
    }
  }
}

// 震动手机
const vibrate = () => {
  if ('vibrate' in navigator) {
    // 震动模式：短-短-长
    navigator.vibrate([100, 50, 100, 50, 200])
  }
}

// 重置状态（中奖后点击继续）
const resetState = () => {
  status.value = 'login'
  userName.value = ''
  ID.value = '' // 【修复】重置时也清空 ID
  prize.value = ''
  // 可以选择断开连接或保持连接
  // if (ws) {
  //   ws.close()
  // }
}

// 重试连接
const retryConnection = () => {
  reconnectAttempts = 0
  status.value = 'login'
  errorMessage.value = ''
  wsConnected = false
  // 关闭旧连接
  if (ws) {
    try {
      ws.close()
    } catch (e) {
      console.log('关闭连接时出错:', e)
    }
    ws = null
  }
  connectWebSocket()
}

// ========== 【修复4】onMounted：只做 iOS 检测，不主动连接 WebSocket ==========
onMounted(() => {
  // 【修复】只检测 iOS 设备，不主动连接 WebSocket
  // iOS 设备必须在用户点击按钮后才能连接
  // 非 iOS 设备也改为在用户点击按钮时连接，保持一致性
  isIOSDevice.value = isIOS()
  
  if (isIOSDevice.value) {
    console.log('检测到 iOS 设备，等待用户点击"加入战场"按钮后连接 WebSocket')
  } else {
    console.log('非 iOS 设备，等待用户点击"加入战场"按钮后连接 WebSocket')
  }
})

onUnmounted(() => {
  // ========== 【为修复 iOS Safari 问题新增】清理心跳定时器 ==========
  stopHeartbeat()
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.mobile-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 登录状态 */
.login-state {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-content {
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.app-title {
  font-size: 48px;
  font-weight: bold;
  color: white;
  margin-bottom: 30px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.ios-hint {
  background: rgba(255, 255, 255, 0.2);
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 30px;
  font-size: 14px;
  color: white;
  line-height: 1.6;
}

.ios-hint p {
  margin: 5px 0;
}

.input-wrapper {
  margin-bottom: 30px;
}

.name-input {
  width: 100%;
  padding: 18px 20px;
  font-size: 18px;
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  outline: none;
  transition: all 0.3s;
}

.name-input:focus {
  background: white;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  transform: translateY(-2px);
}

.name-input::placeholder {
  color: #999;
}
.id-input{
  width: 100%;
  padding: 18px 20px;
  font-size: 18px;
  border: none;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  outline: none;
  transition: all 0.3s;
}
.id-input:focus{
  background: white;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  transform: translateY(-2px);
}
.id-input::placeholder {
  color: #999;
}
.join-button {
  width: 100%;
  padding: 18px;
  font-size: 20px;
  font-weight: bold;
  color: white;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: none;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.join-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.join-button:active:not(:disabled) {
  transform: translateY(0);
}

.join-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 等待状态 */
.waiting-state {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.waiting-content {
  text-align: center;
}

.waiting-icon {
  font-size: 80px;
  margin-bottom: 30px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.waiting-text {
  font-size: 28px;
  color: white;
  font-weight: bold;
  margin-bottom: 40px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.breathing-dot {
  width: 20px;
  height: 20px;
  background: #FFD700;
  border-radius: 50%;
  margin: 0 auto;
  box-shadow: 0 0 20px #FFD700;
  animation: breathing 2s ease-in-out infinite;
}

@keyframes breathing {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.5);
    opacity: 0.7;
  }
}

/* 中奖状态 */
.won-state {
  width: 100%;
  height: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
}

.won-overlay {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF6347 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.won-content {
  text-align: center;
  color: white;
  max-width: 90%;
}

.won-icon {
  font-size: 120px;
  margin-bottom: 30px;
  animation: rotate 1s ease-in-out;
}

@keyframes rotate {
  from {
    transform: rotate(-180deg) scale(0);
  }
  to {
    transform: rotate(0deg) scale(1);
  }
}

.won-title {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 30px;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

.won-prize {
  font-size: 64px;
  font-weight: bold;
  margin-bottom: 30px;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
  background: rgba(255, 255, 255, 0.2);
  padding: 20px 40px;
  border-radius: 15px;
  display: inline-block;
  border: 3px solid white;
  animation: fadeInUp 0.6s ease-out 0.4s both;
}

.won-user-info {
  margin-bottom: 30px;
  animation: fadeInUp 0.6s ease-out 0.6s both;
}

.won-user-name {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.won-user-id {
  font-size: 24px;
  opacity: 0.9;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.back-button {
  padding: 15px 40px;
  font-size: 18px;
  font-weight: bold;
  color: white;
  background: rgba(255, 255, 255, 0.3);
  border: 2px solid white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  animation: fadeInUp 0.6s ease-out 0.8s both;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.back-button:active {
  transform: translateY(0);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 480px) {
  .app-title {
    font-size: 36px;
    margin-bottom: 40px;
  }

  .won-title {
    font-size: 36px;
  }

  .won-prize {
    font-size: 48px;
  }

  .waiting-text {
    font-size: 24px;
  }
}

/* 错误状态 */
.error-state {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.error-content {
  text-align: center;
  color: white;
  max-width: 90%;
}

.error-icon {
  font-size: 80px;
  margin-bottom: 30px;
}

.error-title {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.error-message {
  font-size: 18px;
  margin-bottom: 30px;
  opacity: 0.9;
  line-height: 1.6;
}

.retry-button {
  padding: 15px 40px;
  font-size: 18px;
  font-weight: bold;
  color: white;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: none;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.retry-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.retry-button:active {
  transform: translateY(0);
}
</style>

