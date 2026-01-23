<template>
  <div class="relative h-screen w-screen overflow-hidden text-white" @keydown="handleKeyPress" tabindex="0">

    <!-- 背景视频：永远在最底层，永远可见，抽奖时变模糊变暗 -->
    <video
      src="/bg_video.mp4"
      :class="[
        'absolute inset-0 w-full h-full object-cover transition-all duration-1000 ease-in-out',
        {
          'blur-lg brightness-50 scale-105': isDrawing
        }
      ]"
      style="z-index: -10;"
      autoplay
      loop
      muted
      playsinline
    ></video>

    <!-- 底部 UI 组件层：深色磨砂黑玻风格 -->
    <div class="absolute inset-0 pointer-events-none">
      <!-- 左下角：二维码 -->
      <div class="absolute bottom-6 left-6 z-20 pointer-events-auto">
        <div class="frosted-glass-card p-5">
          <div v-if="qrCodeUrl" class="flex flex-col items-center">
            <QrcodeVue :value="qrCodeUrl" :size="200" level="H" />
            <p class="mt-3 text-sm text-white font-medium text-center">扫码参与抽奖</p>
          </div>
          <div v-else class="w-[200px] h-[200px] flex items-center justify-center text-white">
            加载中...
          </div>
        </div>
      </div>

      <!-- 右下角：在线人数 -->
      <div class="absolute bottom-6 right-6 z-20 pointer-events-auto">
        <div class="frosted-glass-card p-8 text-center">
          <div class="text-5xl font-black text-yellow-400 mb-2">{{ userCount }}</div>
          <div class="text-lg text-white font-medium">当前在线</div>
        </div>
      </div>
    </div>

    <!-- 中间抽奖区域：永远不模糊 -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none" style="transform: translateY(-8%);">
      
      <!-- 左右马匹 GIF：离球更近，形成夹击之势 -->
      <img
        ref="horseLeftRef"
        src="/horse_left.gif"
        alt="Left Horse"
        class="horse-image horse-left"
      />
      <img
        ref="horseRightRef"
        src="/horse_right.gif"
        alt="Right Horse"
        class="horse-image horse-right"
      />

      <!-- 3D 球体容器：金色能量场 -->
      <div ref="sphereContainerRef" class="sphere-container">
        <div ref="sphereWrapperRef" class="sphere-wrapper">
          <!-- 用户名字卡片将通过 JavaScript 动态创建 -->
        </div>
      </div>

      <!-- 中奖者名字显示 -->
      <div v-if="winner" class="winner-name">
        {{ winner }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import confetti from 'canvas-confetti'
import QrcodeVue from 'qrcode.vue'
import { getBackendUrl, getWebSocketUrl, getFrontendUrl } from '../utils/api'
import axios from 'axios'

// 响应式数据
const qrCodeUrl = ref('')
const userCount = ref(0)
const winner = ref('')
const isDrawing = ref(false)
const connectedUsers = ref([])

// DOM 引用
const horseLeftRef = ref(null)
const horseRightRef = ref(null)
const sphereContainerRef = ref(null)
const sphereWrapperRef = ref(null)

// WebSocket 连接
let ws = null

// 动画控制
let sphereRotationAnimation = null
const DRAW_ROTATION_DURATION = 8000 // 8秒旋转时间

// 获取本机 IP 并生成二维码
const fetchIPAndGenerateQR = async () => {
  try {
    const backendUrl = getBackendUrl()
    const response = await axios.get(`${backendUrl}/api/get-ip`)
    const ip = response.data.ip
    
    // 生成二维码 URL
    const frontendUrl = getFrontendUrl()
    if (frontendUrl) {
      qrCodeUrl.value = frontendUrl
    } else {
      // 开发环境：使用获取到的 IP
      qrCodeUrl.value = `http://${ip}:5173/mobile`
    }
  } catch (error) {
    console.error('获取 IP 失败:', error)
    // 降级方案：使用 localhost
    qrCodeUrl.value = 'http://localhost:5173/mobile'
  }
}

// 连接 WebSocket
const connectWebSocket = () => {
  try {
    const wsUrl = getWebSocketUrl('/ws/screen')
    console.log('连接大屏 WebSocket:', wsUrl)
    
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('大屏 WebSocket 连接成功')
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
    }

    ws.onclose = () => {
      console.log('WebSocket 连接关闭，5秒后重连...')
      setTimeout(connectWebSocket, 5000)
    }
  } catch (error) {
    console.error('创建 WebSocket 连接失败:', error)
  }
}

// 处理 WebSocket 消息
const handleMessage = (message) => {
  if (message.type === 'update_count') {
    userCount.value = message.count || 0
    connectedUsers.value = message.users || []
    // 更新球体中的用户卡片
    nextTick(() => {
      initSphere()
    })
  } else if (message.type === 'winner') {
    winner.value = message.name || '未知'
    stopDrawingAnimation()
    // 触发撒花效果
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    })
  }
}

// 触发抽奖
const triggerDraw = () => {
  if (isDrawing.value || !ws || ws.readyState !== WebSocket.OPEN) {
    return
  }

  winner.value = ''
  isDrawing.value = true

  // 发送抽奖请求
  ws.send(JSON.stringify({ type: 'draw' }))

  // 开始动画
  startDrawingAnimation()
}

// 开始抽奖动画
const startDrawingAnimation = () => {
  // 强制重置所有元素状态
  gsap.set([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value, sphereWrapperRef.value], { 
    clearProps: 'all' 
  })
  
  // 手动清除 transform
  if (horseLeftRef.value) horseLeftRef.value.style.transform = ''
  if (horseRightRef.value) horseRightRef.value.style.transform = ''
  if (sphereContainerRef.value) sphereContainerRef.value.style.transform = ''
  if (sphereWrapperRef.value) sphereWrapperRef.value.style.transform = ''

  // 停止所有正在进行的动画
  gsap.killTweensOf([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value, sphereWrapperRef.value])

  // 重置球体缩放
  gsap.set(sphereWrapperRef.value, { 
    scale: 1, 
    scaleX: 1, 
    scaleY: 1, 
    scaleZ: 1 
  })

  // 马匹动画：向中间移动并旋转
  gsap.to(horseLeftRef.value, {
    x: 100,
    y: -100,
    rotation: 12,
    duration: 1,
    ease: 'power2.out'
  })

  gsap.to(horseRightRef.value, {
    x: -100,
    y: -100,
    rotation: -12,
    duration: 1,
    ease: 'power2.out'
  })

  // 球体向上移动
  gsap.to(sphereContainerRef.value, {
    y: -150,
    duration: 1,
    ease: 'power2.out'
  })

  // 加速球体旋转
  if (sphereRotationAnimation) {
    sphereRotationAnimation.timeScale(2)
  }
}

// 停止抽奖动画
const stopDrawingAnimation = () => {
  isDrawing.value = false

  // 马匹返回原位
  gsap.to(horseLeftRef.value, {
    x: 0,
    y: 0,
    rotation: 0,
    duration: 1,
    ease: 'power2.inOut'
  })

  gsap.to(horseRightRef.value, {
    x: 0,
    y: 0,
    rotation: 0,
    duration: 1,
    ease: 'power2.inOut'
  })

  // 球体返回原位
  gsap.to(sphereContainerRef.value, {
    y: 0,
    duration: 1,
    ease: 'power2.inOut'
  })

  // 恢复球体旋转速度
  if (sphereRotationAnimation) {
    sphereRotationAnimation.timeScale(1)
  }
}

// 初始化 3D 球体
const initSphere = () => {
  if (!sphereWrapperRef.value) return

  // 清空现有卡片
  sphereWrapperRef.value.innerHTML = ''

  const users = connectedUsers.value
  if (users.length === 0) return

  // 使用 Fibonacci 球算法均匀分布点
  const points = fibonacciSphere(users.length, 200)

  users.forEach((user, index) => {
    const card = document.createElement('div')
    card.className = 'user-card'
    card.innerHTML = `
      <div class="user-card-content">
        ${user.name || '未知'}
      </div>
    `

    sphereWrapperRef.value.appendChild(card)

    // 设置 3D 位置
    const [x, y, z] = points[index]
    gsap.set(card, {
      x: x,
      y: y,
      z: z
    })
  })
}

// Fibonacci 球算法：在球面上均匀分布点
const fibonacciSphere = (samples, radius) => {
  const points = []
  const phi = Math.PI * (3 - Math.sqrt(5)) // 黄金角度

  for (let i = 0; i < samples; i++) {
    const y = 1 - (i / (samples - 1)) * 2 // y 从 1 到 -1
    const radiusAtY = Math.sqrt(1 - y * y) // 在当前 y 处的圆半径
    const theta = phi * i // 黄金角度旋转

    const x = Math.cos(theta) * radiusAtY * radius
    const z = Math.sin(theta) * radiusAtY * radius
    const yPos = y * radius

    points.push([x, yPos, z])
  }

  return points
}

// 开始球体旋转动画
const startSphereRotation = () => {
  if (!sphereWrapperRef.value) return

  sphereRotationAnimation = gsap.to(sphereWrapperRef.value, {
    rotationY: 360,
    rotationX: 360,
    duration: 20,
    repeat: -1,
    ease: 'none'
  })
}

// 停止球体旋转
const stopSphereRotation = () => {
  if (sphereRotationAnimation) {
    sphereRotationAnimation.kill()
    sphereRotationAnimation = null
  }
}

// 处理键盘事件
const handleKeyPress = (event) => {
  if (event.code === 'Space' && !isDrawing.value) {
    event.preventDefault()
    triggerDraw()
  }
}

// 组件挂载
onMounted(() => {
  fetchIPAndGenerateQR()
  connectWebSocket()
  
  nextTick(() => {
    initSphere()
    startSphereRotation()
  })
})

// 组件卸载
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  stopSphereRotation()
  gsap.killTweensOf([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value, sphereWrapperRef.value])
})
</script>

<style scoped>
/* 深色磨砂黑玻卡片样式 - 统一风格 */
.frosted-glass-card {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1.5rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

/* 马匹图片样式：融合效果，离球更近形成夹击 */
.horse-image {
  position: absolute;
  width: 280px;
  height: 280px;
  object-fit: contain;
  mix-blend-mode: screen !important;
  opacity: 0.9;
  mask-image: radial-gradient(circle, black 60%, transparent 100%);
  -webkit-mask-image: radial-gradient(circle, black 60%, transparent 100%);
  pointer-events: none;
  top: 50%;
  transform: translateY(-50%);
}

.horse-left {
  left: calc(50% - 320px);
}

.horse-right {
  right: calc(50% - 320px);
}

/* 3D 球体容器：450px 金色能量场 */
.sphere-container {
  perspective: 1000px;
  width: 450px;
  height: 450px;
  position: relative;
  z-index: 5;
}

/* 3D 球体包装器 */
.sphere-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d !important;
  transform: translateZ(0);
  border-radius: 50%;
  border: 1px solid rgba(250, 204, 21, 0.3);
  background: radial-gradient(
    circle at center,
    rgba(255, 215, 0, 0.2) 0%,
    rgba(220, 38, 38, 0.0) 70%
  );
  box-shadow: 0 0 60px rgba(250, 204, 21, 0.4);
}

/* 用户名字卡片 */
.user-card {
  position: absolute;
  top: 50%;
  left: 50%;
  transform-style: preserve-3d;
  pointer-events: none;
}

.user-card-content {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(250, 204, 21, 0.4);
  border-radius: 10px;
  padding: 10px 18px;
  color: #FACC15;
  font-size: 1.2rem;
  font-weight: bold;
  white-space: nowrap;
  text-shadow: 
    0 0 12px rgba(250, 204, 21, 0.9),
    0 0 24px rgba(250, 204, 21, 0.7),
    2px 2px 4px rgba(0, 0, 0, 0.9);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

/* 中奖者名字 */
.winner-name {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 9rem;
  font-weight: 900;
  color: #FFD700;
  text-shadow: 
    0 0 20px rgba(255, 215, 0, 0.8),
    0 0 40px rgba(255, 215, 0, 0.6),
    0 0 60px rgba(255, 215, 0, 0.4),
    4px 4px 8px rgba(0, 0, 0, 0.8);
  z-index: 10;
  pointer-events: none;
  filter: drop-shadow(0 0 30px rgba(255, 215, 0, 0.9));
  animation: winnerPop 0.8s ease-out;
}

@keyframes winnerPop {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}
</style>

