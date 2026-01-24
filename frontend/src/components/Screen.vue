<template>
  <div class="relative h-screen w-screen overflow-hidden text-white bg-black" @keydown="handleKeyPress" tabindex="0">

    <!-- 背景视频 -->
    <video
      src="/bg_video.mp4"
      :class="[
        'absolute inset-0 w-full h-full object-cover transition-all duration-1000 ease-in-out',
        {
          'blur-md brightness-[0.4] scale-105': viewMode === 'lottery' && isDrawing
        }
      ]"
      style="z-index: 0;"
      autoplay
      loop
      muted
      playsinline
    ></video>

    <!-- UI 层：深色磨砂黑玻风格 (z-index: 20) -->
    <div class="absolute inset-0 pointer-events-none z-20">

      <!-- 左下角：二维码 -->
      <div class="absolute bottom-8 left-8 pointer-events-auto">
        <div class="glass-panel p-5 flex flex-col items-center animate-fade-in-up">
          <div class="bg-white p-1 rounded-lg">
            <QrcodeVue v-if="qrValue" :value="qrValue" :size="140" level="H" foreground="#000000" />
            <div v-else class="w-[140px] h-[140px] bg-gray-200 animate-pulse"></div>
          </div>
          <p class="mt-3 text-xs text-yellow-400/80 font-bold tracking-widest uppercase">Scan to Join</p>
        </div>
      </div>

      <!-- 右下角：在线人数 -->
      <div class="absolute bottom-8 right-8 pointer-events-auto">
        <div class="glass-panel px-8 py-6 text-center animate-fade-in-up" style="animation-delay: 0.1s;">
          <div class="text-sm text-yellow-400/60 font-bold mb-1 tracking-widest uppercase">Online Users</div>
          <div class="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-yellow-300 to-yellow-600 drop-shadow-[0_4px_10px_rgba(0,0,0,0.5)] font-mono">
            {{ userCount }}
          </div>
        </div>
      </div>

      <!-- 右上角：设置按钮 -->
      <div class="absolute top-8 right-8 pointer-events-auto">
        <button
          @click="showSettings = true"
          class="glass-panel p-4 rounded-full hover:bg-yellow-400/20 transition-colors cursor-pointer"
        >
          <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      <!-- 底部奖项控制栏 (Dock UI) -->
      <div
        class="absolute bottom-0 left-0 right-0 pointer-events-auto transition-opacity duration-300"
        :class="hoverBottomDock ? 'opacity-100' : 'opacity-70'"
        @mouseenter="hoverBottomDock = true"
        @mouseleave="hoverBottomDock = false"
      >
        <div class="flex justify-center mb-8">
          <div class="dock-container bg-black/60 backdrop-blur-xl rounded-full px-8 py-4 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
            <div class="flex gap-3 items-center">
              <button
                v-for="prize in prizes"
                :key="prize.id"
                @click="selectPrize(prize)"
                :disabled="prize.remaining <= 0"
                class="prize-dock-button transition-all duration-200 font-bold text-sm px-6 py-3 rounded-full"
                :class="
                  prize.remaining <= 0
                    ? 'bg-white/10 text-gray-500 cursor-not-allowed opacity-50'
                    : currentPrize?.id === prize.id
                    ? 'bg-gradient-to-r from-[#FDE68A] to-[#F59E0B] text-black shadow-[0_0_20px_rgba(250,204,21,0.6)] scale-105'
                    : 'bg-white/20 text-white hover:bg-white/30'
                "
              >
                <div class="font-bold">{{ prize.name }}</div>
                <div class="text-xs font-normal opacity-80">{{ prize.remaining }}/{{ prize.totalCount }}</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 【Home 模式】显示大标题 ========== -->
    <Transition name="title-fade">
      <div
        v-if="viewMode === 'home'"
        class="absolute inset-0 flex items-center justify-center z-30 pointer-events-none"
      >
        <div class="main-title-container">
          <div class="main-title-year bg-gradient-to-b from-[#FDE68A] via-[#F59E0B] to-[#B45309] bg-clip-text text-transparent drop-shadow-[0_5px_5px_rgba(0,0,0,0.8)]">
            2026
          </div>
          <div class="main-title-subtitle bg-gradient-to-b from-[#FDE68A] via-[#F59E0B] to-[#B45309] bg-clip-text text-transparent drop-shadow-[0_5px_5px_rgba(0,0,0,0.8)] tracking-[1em]">
            聚力同行 · 共创辉煌
          </div>
        </div>
      </div>
    </Transition>

    <!-- ========== 【Lottery 模式】显示马匹和球体 ========== -->
    <Transition name="lottery-fade">
      <div
        v-if="viewMode === 'lottery'"
        class="absolute inset-0 flex items-center justify-center pointer-events-none z-10"
      >
        <!-- 3D 舞台容器 - 核心修复：perspective + flex居中 -->
        <div class="scene-stage">
          <!-- 左马 -->
          <div ref="horseLeftRef" class="horse-wrapper horse-left">
            <img src="/horse_left.gif" class="horse-img" alt="Left Horse" />
          </div>

          <!-- 右马 -->
          <div ref="horseRightRef" class="horse-wrapper horse-right">
            <img src="/horse_right.gif" class="horse-img" alt="Right Horse" />
          </div>

          <!-- 3D 旋转球体 -->
          <div ref="sphereContainerRef" class="sphere-container">
            <div class="sphere-wrapper-center">
              <div ref="sphereWrapperRef" class="sphere-wrapper-3d" :class="{ 'sphere-active': isDrawing }"></div>
            </div>
          </div>
        </div>

        <!-- 底部中间：SPACE 按钮 -->
        <div
          v-if="!winners.length && !isDrawing"
          class="absolute bottom-12 left-1/2 -translate-x-1/2 pointer-events-auto transition-opacity duration-500"
        >
          <div class="px-8 py-3 rounded-full border border-yellow-400/30 bg-black/40 backdrop-blur-md text-yellow-400 font-bold tracking-[0.3em] text-sm shadow-[0_0_30px_rgba(250,204,21,0.2)] animate-pulse cursor-pointer hover:bg-yellow-400/10 transition-colors">
            SPACE TO START
          </div>
        </div>
      </div>
    </Transition>

    <!-- ========== 【批量中奖展示】 ========== -->
    <div
      v-if="winners.length > 0 && !isDrawing"
      class="absolute inset-0 flex items-center justify-center z-40 pointer-events-none"
    >
      <div class="winners-grid-container">
        <!-- 单人：大字体展示 -->
        <div v-if="winners.length === 1" class="single-winner">
          <div class="winner-badge">{{ currentPrize?.name || '一等奖' }}</div>
          <div class="winner-name">{{ winners[0].name }}</div>
          <div v-if="winners[0].id" class="winner-id">工号：{{ winners[0].id }}</div>
        </div>
        <!-- 多人：Grid 布局 -->
        <div v-else class="winners-grid">
          <div
            v-for="(winner, index) in winners"
            :key="index"
            class="winner-card"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="winner-card-name">{{ winner.name }}</div>
            <div v-if="winner.id" class="winner-card-id">{{ winner.id }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置模态框 -->
    <SettingsModal
      v-if="showSettings"
      :prizes="prizes"
      @close="showSettings = false"
      @update="updatePrizes"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import confetti from 'canvas-confetti'
import QrcodeVue from 'qrcode.vue'
import SettingsModal from './SettingsModal.vue'

// ========== 【状态管理】 ==========
const viewMode = ref('home') // 'home' | 'lottery'
const isDrawing = ref(false)
const hoverBottomDock = ref(false)
const showSettings = ref(false)

// ========== 【奖项配置】 ==========
const prizes = ref([
  { id: 1, name: '一等奖', totalCount: 10, batchSize: 1, remaining: 10 },
  { id: 2, name: '二等奖', totalCount: 20, batchSize: 2, remaining: 20 },
  { id: 3, name: '三等奖', totalCount: 20, batchSize: 5, remaining: 20 }
])
const currentPrize = ref(null)
const winners = ref([])

// ========== 【基础状态】 ==========
const qrValue = ref('')
const userCount = ref(0)
const connectedUsers = ref([])

// ========== 【Refs】 ==========
const horseLeftRef = ref(null)
const horseRightRef = ref(null)
const sphereContainerRef = ref(null)
const sphereWrapperRef = ref(null)

// ========== 【常量】 ==========
const SPHERE_RADIUS = 300 // 放大球体半径，让球体更大
let ws = null
let sphereRotationAnim = null
let fastRotationAnim = null // 快速旋转动画（Y轴）
let fastRotationXAnim = null // 快速旋转动画（X轴）
let depthUpdateInterval = null // 深度更新循环

// ========== 【初始化】 ==========
onMounted(() => {
  const origin = window.location.origin
  qrValue.value = `${origin}/mobile`
  initWebSocket()
  
  // 数据填充兜底：如果没有真实用户，强制生成80个假数据
  nextTick(() => {
    if (connectedUsers.value.length === 0) {
      connectedUsers.value = []
      for(let i=0; i<80; i++) {
        connectedUsers.value.push({ 
          name: '虚位以待', 
          id: `fake_${i}`, // 统一为id字段
          employeeId: '',
          isFake: true 
        })
      }
    }
    // 只有在lottery模式才渲染球体
    if (viewMode.value === 'lottery') {
      updateDisplayUsers()
    }
  })

  window.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  if (ws) ws.close()
  window.removeEventListener('keydown', handleKeyPress)
  if (sphereRotationAnim) sphereRotationAnim.kill()
  if (fastRotationAnim) fastRotationAnim.kill()
  if (fastRotationXAnim) fastRotationXAnim.kill()
  stopDynamicDepthUpdate() // 清理深度更新循环
})

// ========== 【WebSocket】 ==========
const initWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const hostname = window.location.hostname
  const port = window.location.port === '5173' ? ':8000' : (window.location.port ? ':' + window.location.port : '')
  const wsUrl = `${protocol}//${hostname}${port}/ws/screen`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'get_users' }))
  }

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'update_count') {
      userCount.value = msg.count
      connectedUsers.value = msg.users || []
      if (viewMode.value === 'lottery') {
        updateDisplayUsers()
      }
    } else if (msg.type === 'draw_result') {
      handleDrawResult(msg)
    }
  }
}

// ========== 【奖项选择】 ==========
const selectPrize = (prize) => {
  if (prize.remaining <= 0) return
  
  currentPrize.value = prize
  viewMode.value = 'lottery'
  winners.value = []
  
  // 淡入动画
  nextTick(() => {
    if (horseLeftRef.value && horseRightRef.value && sphereContainerRef.value) {
      gsap.fromTo([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value], 
        { opacity: 0 },
        { opacity: 1, duration: 0.8, ease: 'power2.out' }
      )
    }
    updateDisplayUsers()
    // 确保球体渲染后再启动旋转
    setTimeout(() => {
      startIdleRotation()
    }, 300)
  })
}

// ========== 【抽奖逻辑】 ==========
const startDraw = async () => {
  if (!currentPrize.value || currentPrize.value.remaining <= 0) return
  if (isDrawing.value) return

  isDrawing.value = true
  winners.value = []

  // 调用后端API
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
  const hostname = window.location.hostname
  const port = window.location.port === '5173' ? ':8000' : (window.location.port ? ':' + window.location.port : '')
  const apiUrl = `${protocol}//${hostname}${port}/api/draw`

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        count: currentPrize.value.batchSize,
        prize_name: currentPrize.value.name
      })
    })

    const data = await response.json()
    if (data.success) {
      // 更新剩余数量
      currentPrize.value.remaining -= data.count
      // 平滑减速：让球体慢慢停下来
      setTimeout(() => {
        stopRotationSmoothly()
      }, 3500) // 在抽奖进行到3.5秒时开始减速
      
      // 延迟显示结果（动画效果）
      setTimeout(() => {
        isDrawing.value = false
        winners.value = data.winners
        // 撒花
        confetti({
          particleCount: 200,
          spread: 90,
          origin: {y: 0.5},
          colors: ['#FFD700', '#FFA500', '#FF6347', '#FF1493']
        })
      }, 5500) // 3.5秒开始减速 + 2秒减速时间 = 5.5秒
    }
  } catch (error) {
    console.error('抽奖失败:', error)
    isDrawing.value = false
  }

  // 动画逻辑
  gsap.killTweensOf([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value])

  if (horseLeftRef.value) {
    gsap.set(horseLeftRef.value, { x: 0, y: 0, rotation: 0, clearProps: 'transform' })
    gsap.to(horseLeftRef.value, {
      x: 30, y: -180, rotation: -20,
      duration: 1.0, ease: 'power3.out', force3D: true
    })
  }

  if (horseRightRef.value) {
    gsap.set(horseRightRef.value, { x: 0, y: 0, rotation: 0, clearProps: 'transform' })
    gsap.to(horseRightRef.value, {
      x: -30, y: -180, rotation: 20,
      duration: 1.0, ease: 'power3.out', force3D: true
    })
  }

  if (sphereContainerRef.value) {
    // 保持球体在马匹上方，不修改GIF逻辑
    // 球体初始位置是 translateY(-60px)，抽奖时向上移动
    gsap.set(sphereContainerRef.value, { y: -60, scale: 1, clearProps: 'transform' })
    gsap.to(sphereContainerRef.value, {
      y: -120, scale: 1.1, // 向上移动，但更靠近马匹
      duration: 1.0, ease: 'power3.out'
    })
  }

  startFastRotation()
}

// ========== 【键盘事件】 ==========
const handleKeyPress = (e) => {
  if (e.code === 'Space') {
    e.preventDefault()
    if (viewMode.value === 'home') {
      // Home模式，不做任何事
      return
    } else if (winners.length > 0) {
      // 关闭结果展示，回到准备模式
      winners.value = []
      if (currentPrize.value && currentPrize.value.remaining > 0) {
        // 如果还有剩余，保持在lottery模式
        viewMode.value = 'lottery'
      } else {
        // 如果抽完了，回到home模式
        viewMode.value = 'home'
        currentPrize.value = null
      }
    } else if (!isDrawing.value) {
      // 开始抽奖
      startDraw()
    }
  }
}

// ========== 【3D 球体逻辑】 ==========
const updateDisplayUsers = () => {
  if (viewMode.value !== 'lottery') return
  
  // 1️⃣ 统一用户对象格式 - normalize数据
  let displayList = connectedUsers.value.map(u => ({
    userId: u.id || u.userId || `user_${Date.now()}_${Math.random()}`, // 统一为userId
    name: u.name || '未知',
    employeeId: u.employeeId || u.employee_id || '',
    isFake: false
  }))
  
  // 2️⃣ 如果少于50人，补齐假数据
  const minCount = 50
  if (displayList.length < minCount) {
    const needFake = minCount - displayList.length
    for(let i=0; i<needFake; i++) {
      displayList.push({ 
        userId: `fake_${i}`, // 统一为userId
        name: '虚位以待', 
        employeeId: '',
        isFake: true 
      })
    }
  }
  
  renderSphere(displayList)
}

// 斐波那契球算法 - 改进版本（添加轻微抖动使分布更自然）
const fibonacciSphere = (i, n, R) => {
  const goldenAngle = Math.PI * (3 - Math.sqrt(5)) // 黄金角度
  const theta = goldenAngle * i // 方位角
  const y = 1 - (2 * i) / (n - 1) // y坐标从1到-1
  const radiusAtY = Math.sqrt(1 - y * y) // 在当前y高度的圆半径
  
  // 添加轻微随机扰动，使分布更自然
  const jitter = 0.02 // 2%的随机扰动
  const randomTheta = (Math.random() - 0.5) * jitter
  const randomY = (Math.random() - 0.5) * jitter
  
  return {
    x: R * radiusAtY * Math.cos(theta + randomTheta),
    y: R * (y + randomY),
    z: R * radiusAtY * Math.sin(theta + randomTheta)
  }
}

const renderSphere = (users) => {
  if (!sphereWrapperRef.value) {
    setTimeout(() => renderSphere(users), 100)
    return
  }
  
  if (isDrawing.value) return
  
  sphereWrapperRef.value.innerHTML = ''

  users.forEach((user, i) => {
    // 使用改进后的斐波那契球算法
    const pos = fibonacciSphere(i, users.length, SPHERE_RADIUS)
    const el = document.createElement('div')
    el.className = 'user-card-3d'
    
    if (user.isFake) {
      el.classList.add('user-card-fake')
    }
    
    // 只显示名字和工号，不显示 ID
    const nameEl = document.createElement('div')
    nameEl.className = 'name'
    nameEl.textContent = user.name || '未知'
    
    el.appendChild(nameEl)
    
    // 只有真用户才显示工号
    if (!user.isFake && user.employeeId) {
      const idEl = document.createElement('div')
      idEl.className = 'id'
      idEl.textContent = user.employeeId
      el.appendChild(idEl)
    }
    
    // ========== 【关键：为后续收集用户ID + 名字做好结构】 ==========
    // 2️⃣ 渲染时明确绑定userId和name（为后端抽奖准备）
    el.setAttribute('data-user-id', user.userId)
    el.setAttribute('data-user-name', user.name)
    // 👉 这一步非常关键：后面要做的任何事情（定位中奖人、定格、发光、从球体中"抽出来"）都靠它
    
    // ========== 【关键修复：卡片作为球体表面的贴图，只使用translate3d定位】 ==========
    // 先设置初始位置（中心点）
    el.style.left = '50%'
    el.style.top = '50%'
    el.style.marginLeft = '-70px' // 更新为新的宽度的一半
    el.style.marginTop = '-22px' // 更新为新的高度的一半
    
    // ========== 【计算深度效果】根据z坐标调整透明度和缩放 ==========
    // z坐标范围：-SPHERE_RADIUS 到 SPHERE_RADIUS
    // 归一化到 0-1：z值越大（越靠近观察者），值越大
    const normalizedZ = (pos.z + SPHERE_RADIUS) / (2 * SPHERE_RADIUS) // 0到1
    const depthOpacity = 0.4 + normalizedZ * 0.6 // 背面0.4，正面1.0
    const depthScale = 0.7 + normalizedZ * 0.3 // 背面0.7，正面1.0
    
    // ========== 【关键修复：移除卡片独立旋转，只使用translate3d定位】 ==========
    // 卡片应该作为球体表面的"贴图"，随着球体旋转而自然移动
    // 不计算rotationX和rotationY，让卡片自然跟随球体旋转
    gsap.set(el, {
      x: pos.x,
      y: pos.y,
      z: pos.z,
      // 不设置 rotationX 和 rotationY，让卡片自然粘附在球面
      scale: depthScale,
      opacity: depthOpacity,
      transformStyle: 'preserve-3d',
      force3D: true,
      immediateRender: true
    })
    
    // 存储初始位置，用于动态深度更新
    el.setAttribute('data-initial-x', pos.x.toString())
    el.setAttribute('data-initial-y', pos.y.toString())
    el.setAttribute('data-initial-z', pos.z.toString())
    el.setAttribute('data-depth', normalizedZ.toFixed(2))

    sphereWrapperRef.value.appendChild(el)
  })
  
  console.log(`已渲染 ${users.length} 个3D卡片，形成立体球体`)
}

const startIdleRotation = () => {
  if (!sphereWrapperRef.value) {
    setTimeout(() => startIdleRotation(), 100)
    return
  }
  
  // 如果动画已存在且正在运行，只重置速度
  if (sphereRotationAnim && sphereRotationAnim.isActive()) {
    sphereRotationAnim.timeScale(1)
    return
  }
  
  // 清理旧动画
  if (sphereRotationAnim) {
    sphereRotationAnim.kill()
  }

  // 创建新的旋转动画 - GSAP只负责旋转，不负责居中
  sphereRotationAnim = gsap.to(sphereWrapperRef.value, {
    rotationY: 360,
    rotationX: -60,
    duration: 20,
    repeat: -1,
    ease: 'none',
    force3D: true // 强制硬件加速
  })
  
  // 启动动态深度更新
  startDynamicDepthUpdate()
  
  console.log('球体旋转动画已启动')
}

const startFastRotation = () => {
  if (!sphereWrapperRef.value) {
    console.warn('sphereWrapperRef 未准备好')
    return
  }
  
  // 1. Kill 掉当前的待机动画
  if (sphereRotationAnim && sphereRotationAnim.isActive()) {
    sphereRotationAnim.kill()
    sphereRotationAnim = null
  }
  
  // 2. Kill 掉可能存在的旧快速旋转动画
  if (fastRotationAnim) {
    fastRotationAnim.kill()
    fastRotationAnim = null
  }
  if (fastRotationXAnim) {
    fastRotationXAnim.kill()
    fastRotationXAnim = null
  }
  
  // 3. 添加快速旋转类名（❌ 已移除 filter: blur()，会创建新的渲染层）
  sphereWrapperRef.value.classList.add('sphere-active')
  
  // 4. 创建新的疯狂旋转动画 - Y轴高速匀速旋转
  const currentRotationY = gsap.getProperty(sphereWrapperRef.value, "rotationY") || 0
  
  fastRotationAnim = gsap.fromTo(sphereWrapperRef.value, 
    {
      rotationY: currentRotationY
    },
    {
      rotationY: currentRotationY + 360, // 转1圈
      duration: 0.5, // 高速旋转：0.5秒转1圈（2圈/秒）
      ease: "none", // 匀速旋转
      repeat: -1,
      force3D: true,
      immediateRender: false
    }
  )
  
  // 5. X轴混乱翻滚 - 小幅度正弦摆动（制造混沌）
  const currentRotationX = gsap.getProperty(sphereWrapperRef.value, "rotationX") || -60
  const randomX = gsap.utils.random(-20, 20) // 小幅度摆动
  
  fastRotationXAnim = gsap.fromTo(sphereWrapperRef.value,
    {
      rotationX: currentRotationX
    },
    {
      rotationX: currentRotationX + randomX,
      duration: 0.6, // 正弦摆动速度
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut", // 正弦缓动，制造混沌感
      force3D: true,
      immediateRender: false
    }
  )
  
  // 6. 启动动态深度更新（快速旋转时也需要）
  startDynamicDepthUpdate()
  
  // 7. 确保所有卡片可见
  const cards = sphereWrapperRef.value.querySelectorAll('.user-card-3d')
  cards.forEach(card => {
    // 不强制设置opacity，让动态深度更新来控制
  })
  
  console.log('球体开始疯狂旋转！')
}

const handleDrawResult = (msg) => {
  // WebSocket返回的结果处理
  if (msg.type === 'draw_result' && msg.winners) {
    // 更新剩余数量
    if (currentPrize.value) {
      currentPrize.value.remaining -= msg.winners.length
    }
    
    // 惯性刹车：平滑减速并回正
    stopRotationSmoothly()
    
    // 延迟显示结果（动画效果）
    setTimeout(() => {
      isDrawing.value = false
      winners.value = msg.winners
      // 撒花
      confetti({
        particleCount: 200,
        spread: 90,
        origin: {y: 0.5},
        colors: ['#FFD700', '#FFA500', '#FF6347', '#FF1493']
      })
    }, 2000) // 等待2秒减速完成
  }
}

// 平滑停止旋转的独立函数
const stopRotationSmoothly = () => {
  if (!sphereWrapperRef.value) return
  
  // 0. 停止动态深度更新
  stopDynamicDepthUpdate()
  
  // 1. 移除快速旋转类名（❌ 已移除 filter: blur()）
  if (sphereWrapperRef.value) {
    sphereWrapperRef.value.classList.remove('sphere-active')
  }
  
  // 2. 先停止X轴摆动，再减速Y轴
  // 先停止X轴摆动并回正
  const currentX = gsap.getProperty(sphereWrapperRef.value, "rotationX") || 0
  if (fastRotationXAnim) {
    fastRotationXAnim.kill()
    fastRotationXAnim = null
  }
  gsap.to(sphereWrapperRef.value, {
    rotationX: 0, // 回正到0度
    duration: 1,
    ease: "power2.out",
    force3D: true
  })
  
  // 3. 获取当前Y轴旋转角度并平滑减速
  const currentRotationY = gsap.getProperty(sphereWrapperRef.value, "rotationY") || 0
  
  // 4. Kill Y轴旋转动画
  if (fastRotationAnim) {
    fastRotationAnim.kill()
    fastRotationAnim = null
  }
  
  // 5. 平滑减速Y轴旋转
  gsap.to(sphereWrapperRef.value, {
    rotationY: currentRotationY, // 保持当前角度，停止旋转
    duration: 2,
    ease: "power2.out",
    force3D: true,
    onComplete: () => {
      // 停止后，恢复所有卡片的正常显示
      const cards = sphereWrapperRef.value.querySelectorAll('.user-card-3d')
      cards.forEach(card => {
        // 移除模糊，恢复正常显示
        gsap.set(card, { opacity: 1, scale: 1, filter: 'blur(0px)' })
      })
    }
  })
  
  console.log('球体开始平滑减速并回正')
}

const updatePrizes = (newPrizes) => {
  // 重置所有奖项的剩余数量为总数（重置抽奖进度）
  const updatedPrizes = newPrizes.map(prize => ({
    ...prize,
    remaining: prize.totalCount // 重置为总数
  }))
  
  prizes.value = updatedPrizes
  
  // 如果当前选中的奖项还存在，更新引用
  if (currentPrize.value) {
    const found = updatedPrizes.find(p => p.id === currentPrize.value.id)
    if (found) {
      currentPrize.value = found
    } else {
      // 如果当前奖项被删除，回到home模式
      currentPrize.value = null
      viewMode.value = 'home'
      winners.value = []
    }
  }
}

// ========== 【动态深度更新 - 实时计算Z轴深度，确保3D效果】 ==========
const startDynamicDepthUpdate = () => {
  // 停止旧的更新循环
  stopDynamicDepthUpdate()
  
  // 使用 requestAnimationFrame 实现更流畅的更新（约60fps）
  let animationFrameId = null
  
  const updateDepth = () => {
    if (!sphereWrapperRef.value) {
      stopDynamicDepthUpdate()
      return
    }
    
    const cards = sphereWrapperRef.value.querySelectorAll('.user-card-3d')
    if (cards.length === 0) {
      animationFrameId = requestAnimationFrame(updateDepth)
      return
    }
    
    // 获取球体的当前旋转角度
    const rotationY = gsap.getProperty(sphereWrapperRef.value, "rotationY") || 0
    const rotationX = gsap.getProperty(sphereWrapperRef.value, "rotationX") || 0
    
    cards.forEach(card => {
      // 获取卡片的初始位置（球面上的位置）
      const initialX = parseFloat(card.getAttribute('data-initial-x') || '0')
      const initialY = parseFloat(card.getAttribute('data-initial-y') || '0')
      const initialZ = parseFloat(card.getAttribute('data-initial-z') || '0')
      
      // 计算旋转后的实际z坐标（相对于观察者）
      // 使用旋转矩阵：先绕Y轴旋转，再绕X轴旋转
      const radY = (rotationY * Math.PI) / 180
      const radX = (rotationX * Math.PI) / 180
      
      let x = initialX
      let y = initialY
      let z = initialZ
      
      // Y轴旋转（绕Y轴）
      const cosY = Math.cos(radY)
      const sinY = Math.sin(radY)
      const tempX = x * cosY + z * sinY
      const tempZ = -x * sinY + z * cosY
      x = tempX
      z = tempZ
      
      // X轴旋转（绕X轴）
      const cosX = Math.cos(radX)
      const sinX = Math.sin(radX)
      const finalY = y * cosX - z * sinX
      const finalZ = y * sinX + z * cosX
      
      // 根据旋转后的z坐标计算深度效果
      // z坐标范围：-SPHERE_RADIUS 到 SPHERE_RADIUS
      const normalizedZ = (finalZ + SPHERE_RADIUS) / (2 * SPHERE_RADIUS) // 0到1
      const depthOpacity = 0.3 + normalizedZ * 0.7 // 背面0.3，正面1.0（远暗近亮）
      const depthScale = 0.6 + normalizedZ * 0.4 // 背面0.6，正面1.0（远小近大）
      
      // 根据深度添加模糊效果（背面更模糊）
      const depthBlur = (1 - normalizedZ) * 2 // 背面2px，正面0px
      
      // 更新卡片的透明度和缩放
      gsap.set(card, {
        opacity: depthOpacity,
        scale: depthScale,
        filter: `blur(${depthBlur}px)` // 根据深度添加模糊
      })
    })
    
    // 继续下一帧
    animationFrameId = requestAnimationFrame(updateDepth)
  }
  
  // 启动更新循环
  animationFrameId = requestAnimationFrame(updateDepth)
  depthUpdateInterval = animationFrameId // 存储ID用于清理
}

const stopDynamicDepthUpdate = () => {
  if (depthUpdateInterval) {
    cancelAnimationFrame(depthUpdateInterval)
    depthUpdateInterval = null
  }
}
</script>

<style scoped>
/* ========== 【基础样式】 ========== */
.glass-panel {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

/* ========== 【大标题样式】流光金渐变 + 两行排版 ========== */
.main-title-container {
  text-align: center;
}

.main-title-year {
  font-size: 180px;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 20px;
  letter-spacing: 0.05em;
}

.main-title-subtitle {
  font-size: 64px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 1em;
}

/* ========== 【底部Dock样式】悬浮底座风格 ========== */
.dock-container {
  display: inline-flex;
  align-items: center;
}

.prize-dock-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 100px;
  transition: all 0.2s ease;
}

.prize-dock-button:not(:disabled):hover {
  transform: translateY(-2px);
}

/* ========== 【3D 舞台容器 - 透视必须来自父级舞台】 ========== */
.scene-stage {
  position: relative;
  width: 100%;
  height: 100%;
  perspective: 2000px !important; /* 透视必须来自父级舞台 */
  perspective-origin: center center; /* 透视原点 */
  display: flex; /* 强制flex布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  transform-style: preserve-3d; /* 确保3D变换传递 */
}

/* ========== 【马匹样式】 ========== */
.horse-wrapper {
  position: absolute;
  top: calc(50% + 160px);
  width: 320px;
  height: auto;
  will-change: transform;
  transform: translateY(-50%); /* ❌ 已移除 translateZ(0)（会强制2D合成） */
  pointer-events: none;
}

.horse-left {
  left: calc(50% - 400px);
}

.horse-right {
  right: calc(50% - 400px);
}

.horse-img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
  opacity: 0.8;
  mix-blend-mode: screen !important;
  filter: contrast(1.5) brightness(1.2);
  mask-image: radial-gradient(closest-side, black 30%, transparent 100%);
  -webkit-mask-image: radial-gradient(closest-side, black 30%, transparent 100%);
  mask-size: cover;
  -webkit-mask-size: cover;
  mask-position: center;
  -webkit-mask-position: center;
  pointer-events: none;
}

/* ========== 【球体容器】确保在GIF上方 + 不设置perspective（透视来自父级）】 ========== */
.sphere-container {
  position: relative;
  width: 440px;
  height: 440px;
  z-index: 20; /* 确保在马匹上方 */
  transform: translateY(-60px); /* 更靠近马匹 */
  transform-style: preserve-3d !important; /* 关键：确保3D效果传递 */
  /* ❌ 不允许在球体容器上设置 perspective，透视必须来自 .scene-stage */
}

/* ========== 【居中容器 - 只负责居中，不参与3D变换】 ========== */
.sphere-wrapper-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform: translate(-50%, -50%); /* 绝对居中 */
  transform-style: preserve-3d; /* 确保3D变换传递 */
}

/* ========== 【3D旋转容器 - 摄像机后移 + 旋转（无背景，纯3D球体）】 ========== */
.sphere-wrapper-3d {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform: translate(-50%, -50%) translateZ(-600px); /* 关键：摄像机后退 */
  transform-style: preserve-3d !important; /* 强制3D属性 - 关键：确保子元素3D变换生效 */
  transform-origin: center center; /* 旋转中心 */
  /* ⛔ 删除背景 - 去掉红色扁平圆 */
  background: none;
  /* ⛔ 删除内发光 */
  box-shadow: none;
  border-radius: 0;
  will-change: transform, rotationY, rotationX; /* 优化性能 */
  /* ❌ 已移除 backface-visibility: hidden（会裁掉Z深度） */
  /* ❌ 已移除 filter: blur()（会创建新的渲染层） */
  /* 确保子元素正确继承3D变换 */
  -webkit-transform-style: preserve-3d;
}

/* ========== 【Active 状态样式 - 清空所有视觉效果】 ========== */
.sphere-wrapper-3d.sphere-active {
  /* ⛔ 清空所有视觉效果，保持纯3D球体 */
  background: none;
  box-shadow: none;
  border: none;
}

/* ========== 【呼吸动画】 ========== */
@keyframes pulseSphere {
  from {
    transform: translate(-50%, -50%) scale(1);
  }
  to {
    transform: translate(-50%, -50%) scale(1.05);
  }
}

/* ========== 【3D 卡片样式 - 放大尺寸 + 增强立体感 + 确保正确继承3D变换】 ========== */
.user-card-3d {
  position: absolute;
  left: 50%;
  top: 50%;
  margin-left: -70px; /* width / 2 = 140 / 2 */
  margin-top: -22px; /* min-height / 2 = 44 / 2 */
  width: 140px; /* 原 100px，放大40% */
  min-height: 44px; /* 原 30px，放大47% */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  /* 添加背景渐变和阴影，增强立体感 */
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.6) 0%,
    rgba(0, 0, 0, 0.4) 50%,
    rgba(0, 0, 0, 0.6) 100%
  );
  backdrop-filter: blur(4px);
  border: 1px solid rgba(250, 204, 21, 0.3);
  border-radius: 10px; /* 原 6px，放大67% */
  padding: 8px 10px; /* 原 4px 6px，放大 */
  /* 根据深度添加阴影 */
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.5),
    0 0 12px rgba(250, 204, 21, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  opacity: 1;
  will-change: transform, opacity; /* 优化性能 */
  transform-style: preserve-3d; /* 强制3D属性 - 确保作为球体表面的贴图 */
  backface-visibility: visible; /* 背面可见 - 确保旋转时能看到 */
  white-space: nowrap; /* 防止文字换行 */
  /* 关键：不设置独立的旋转，让卡片自然跟随球体旋转 */
  transform-origin: center center;
  /* 确保硬件加速 */
  -webkit-transform-style: preserve-3d;
  -webkit-backface-visibility: visible;
}

/* ========== 【根据深度调整卡片样式】 ========== */
.user-card-3d[data-depth] {
  /* 深度效果通过JS动态设置opacity和scale */
}

/* ========== 【假数据卡片样式】 ========== */
.user-card-3d.user-card-fake {
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.3) 0%,
    rgba(0, 0, 0, 0.2) 50%,
    rgba(0, 0, 0, 0.3) 100%
  );
  border-color: rgba(250, 204, 21, 0.15);
  box-shadow: 
    0 1px 4px rgba(0, 0, 0, 0.3),
    0 0 6px rgba(250, 204, 21, 0.1);
}

.user-card-3d .name {
  font-size: 18px; /* 原 14px，放大29% */
  font-weight: 700;
  color: #F59E0B; /* 金色文字 */
  text-shadow: 
    0 0 4px rgba(245, 158, 11, 0.9),
    0 0 8px rgba(245, 158, 11, 0.6),
    0 2px 4px rgba(0, 0, 0, 0.8);
  line-height: 1.2;
  white-space: nowrap;
}

.user-card-3d .id {
  font-size: 13px; /* 原 10px，放大30% */
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  text-shadow: 
    0 0 2px rgba(255, 255, 255, 0.6),
    0 1px 2px rgba(0, 0, 0, 0.8);
  line-height: 1.2;
  white-space: nowrap;
}

.user-card-3d.user-card-fake .name {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  text-shadow: 
    0 0 2px rgba(255, 255, 255, 0.3),
    0 1px 2px rgba(0, 0, 0, 0.6);
}

/* ========== 【批量中奖展示】 ========== */
.winners-grid-container {
  width: 90%;
  max-width: 1200px;
}

.single-winner {
  text-align: center;
}

.winners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  padding: 40px;
}

.winner-card {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  border: 2px solid rgba(250, 204, 21, 0.5);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(250, 204, 21, 0.3);
  animation: popIn 0.5s ease-out;
}

.winner-card-name {
  font-size: 28px;
  font-weight: 800;
  color: #FFD700;
  margin-bottom: 8px;
}

.winner-card-id {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
}

.winner-badge {
  display: inline-block;
  background: linear-gradient(to right, #dc2626, #991b1b);
  border: 2px solid #facc15;
  color: white;
  padding: 8px 30px;
  border-radius: 50px;
  font-size: 24px;
  font-weight: bold;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
  margin-bottom: 20px;
}

.winner-name {
  font-size: 120px;
  font-weight: 900;
  color: white;
  text-transform: uppercase;
  background: linear-gradient(to bottom, #ffffff, #facc15);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 5px 0 #b45309) drop-shadow(0 20px 40px rgba(0, 0, 0, 0.8));
}

.winner-id {
  font-size: 32px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 20px;
}

/* ========== 【动画】 ========== */
.title-fade-enter-active {
  animation: fadeInUp 1s ease-out;
}

.title-fade-leave-active {
  animation: fadeOut 0.5s ease-in;
}

.lottery-fade-enter-active {
  animation: fadeIn 0.8s ease-out;
}

.lottery-fade-leave-active {
  animation: fadeOut 0.5s ease-in;
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

@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-30px);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.8s ease-out;
}
</style>
