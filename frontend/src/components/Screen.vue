<template>
  <div class="relative h-screen w-screen overflow-hidden text-white bg-black" @keydown="handleKeyPress" @click="handleGlobalClick" tabindex="0">

    <!-- 背景视频 -->
    <video
      src="/bg_video.mp4"
      :class="[
        'absolute inset-0 w-full h-full object-cover transition-all duration-1000 ease-in-out',
        {
          'blur-[60px] brightness-[0.4] scale-125': viewMode === 'lottery' || isDrawing || winners.length > 0
        }
      ]"
      style="z-index: 0;"
      autoplay
      loop
      muted
      playsinline
    ></video>

    <!-- 抽奖时的背景遮罩层 - 增强虚化效果 -->
    <div
      v-if="viewMode === 'lottery' || isDrawing || winners.length > 0"
      class="absolute inset-0 bg-black/60 transition-opacity duration-1000 ease-in-out"
      style="z-index: 1;"
    ></div>

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

      <!-- 右上角：设置按钮、导入按钮和导出按钮 -->
      <div class="absolute top-8 right-8 pointer-events-auto flex gap-3">
        <button
          @click="exportWinnersToExcel"
          class="glass-panel p-4 rounded-full hover:bg-green-400/20 transition-colors cursor-pointer"
          title="导出中奖名单"
        >
          <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>
        
        <button
          @click="handleOpenImportModal"
          class="glass-panel p-4 rounded-full hover:bg-blue-400/20 transition-colors cursor-pointer"
          title="导入人员名单"
        >
          <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>
        
        <button
          @click="showSettings = true"
          class="glass-panel p-4 rounded-full hover:bg-yellow-400/20 transition-colors cursor-pointer"
          title="设置"
        >
          <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      <!-- 右侧奖项控制栏 (垂直排列) -->
      <div
        class="absolute top-24 right-8 pointer-events-auto transition-opacity duration-300"
        :class="hoverBottomDock ? 'opacity-100' : 'opacity-70'"
        @mouseenter="hoverBottomDock = true"
        @mouseleave="hoverBottomDock = false"
      >
        <div class="prize-sidebar-container bg-black/60 backdrop-blur-xl rounded-2xl px-4 py-4 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
          <div class="flex flex-col gap-3">
            <button
              v-for="prize in prizes"
              :key="prize.id"
              @click="selectPrize(prize)"
              :disabled="prize.remaining <= 0"
              class="prize-sidebar-button transition-all duration-200 font-bold text-sm px-5 py-3 rounded-xl w-full"
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

    <!-- ========== 【Home 模式】显示大标题 ========== -->
    <!-- 已删除标题文字 -->

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
            <div ref="sphereWrapperRef" class="sphere-wrapper" :class="{ 'sphere-active': isDrawing }"></div>
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
      class="absolute inset-0 flex items-center justify-center z-40 pointer-events-auto"
    >
      <div class="winners-grid-container">
        <!-- 单人：大字体展示 -->
        <div v-if="winners.length === 1" class="single-winner">
          <div class="winner-badge">{{ currentPrize?.name || '一等奖' }}</div>
          <div class="winner-name">{{ winners[0].name || winners[0].userName || '未知' }}</div>
          <div v-if="winners[0].employeeId || winners[0].employee_id || winners[0].id" class="winner-id">
            工号：{{ winners[0].employeeId || winners[0].employee_id || winners[0].id }}
          </div>
        </div>
        <!-- 多人：Grid 布局 -->
        <div v-else class="winners-grid">
          <div
            v-for="(winner, index) in winners"
            :key="index"
            class="winner-card"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="winner-card-name">{{ winner.name || winner.userName || '未知' }}</div>
            <div v-if="winner.employeeId || winner.employee_id || winner.id" class="winner-card-id">
              {{ winner.employeeId || winner.employee_id || winner.id }}
            </div>
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

    <!-- 导入人员模态框 -->
    <ImportModal
      :show="showImportModal"
      @close="showImportModal = false"
      @import="importUsersData"
    />

    <!-- 成功提示模态框 -->
    <Transition name="modal-fade">
      <div
        v-if="showSuccessToast"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
        @click.self="showSuccessToast = false"
      >
        <div class="glass-panel px-8 py-6 rounded-2xl border-2 border-green-400/50 shadow-[0_0_30px_rgba(34,197,94,0.5)] max-w-md mx-4">
          <div class="flex flex-col items-center gap-4">
            <svg class="w-16 h-16 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <p class="text-xl font-bold text-white text-center whitespace-pre-line">{{ successMessage }}</p>
            <button
              @click="showSuccessToast = false"
              class="px-8 py-3 rounded-lg bg-gradient-to-r from-green-500 to-green-600 text-white font-bold hover:opacity-90 transition-opacity mt-2"
            >
              确定
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import confetti from 'canvas-confetti'
import QrcodeVue from 'qrcode.vue'
import SettingsModal from './SettingsModal.vue'
import ImportModal from './ImportModal.vue'

// ========== 【状态管理】 ==========
const viewMode = ref('home') // 'home' | 'lottery'
const isDrawing = ref(false)
const hoverBottomDock = ref(false)
const showSettings = ref(false)
const showImportModal = ref(false)
const successMessage = ref('')
const showSuccessToast = ref(false)

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
const connectedUsers = ref([]) // WebSocket登录的用户
const importedUsers = ref([]) // 导入的用户数据（模拟数据）
const hasImportedData = ref(false) // 是否有导入数据

// ========== 【中奖人员记录】 ==========
const allWinners = ref([]) // 记录所有中奖人员，用于导出Excel

// ========== 【Refs】 ==========
const horseLeftRef = ref(null)
const horseRightRef = ref(null)
const sphereContainerRef = ref(null)
const sphereWrapperRef = ref(null)

// ========== 【常量】 ==========
const SPHERE_RADIUS = 250 // 增大球体半径，增强立体感
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
          id: `fake_${i}`,
          userId: `fake_${i}`,
          employeeId: `F${i.toString().padStart(4, '0')}`,
          isFake: true 
        })
      }
    }
    
    // 【关键修复】无论什么模式，都初始化球体显示
    setTimeout(() => {
      // 确保DOM已经渲染
      if (viewMode.value === 'lottery') {
        updateDisplayUsers()
        // 启动空闲旋转
        startIdleRotation()
      }
    }, 500)
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
    console.log('【WebSocket】连接成功:', wsUrl)
    ws.send(JSON.stringify({ type: 'get_users' }))
  }

  ws.onerror = (error) => {
    console.error('【WebSocket】连接错误:', error)
  }

  ws.onclose = (event) => {
    console.warn('【WebSocket】连接关闭:', event.code, event.reason)
    // 尝试重连
    setTimeout(() => {
      console.log('【WebSocket】尝试重新连接...')
      initWebSocket()
    }, 3000)
  }

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'update_count') {
      userCount.value = msg.count
      // 【关键修复】如果有导入数据，不使用WebSocket登录数据
      // 只有在没有导入数据时，才使用WebSocket登录数据
      if (!hasImportedData.value) {
        // 过滤掉已中奖的人员
        const existingWinnerIds = new Set(allWinners.value.map(w => w.userId))
        connectedUsers.value = (msg.users || []).filter(u => 
          !existingWinnerIds.has(u.id || u.userId)
        )
        if (viewMode.value === 'lottery') {
          updateDisplayUsers()
        }
      } else {
        console.log('【WebSocket】检测到导入数据，忽略WebSocket登录用户更新')
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
  
  // 重置马匹和球体位置
  resetHorseAndSpherePosition()
  
  // 淡入动画
  nextTick(() => {
    if (horseLeftRef.value && horseRightRef.value && sphereContainerRef.value) {
      gsap.fromTo([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value], 
        { opacity: 0 },
        { opacity: 1, duration: 0.8, ease: 'power2.out' }
      )
    }
    // 【关键修复】确保更新球体显示
    updateDisplayUsers()
    
    // 确保球体渲染后再启动旋转
    setTimeout(() => {
      startIdleRotation()
    }, 300)
  })
}

// ========== 【重置马匹和球体位置】 ==========
const resetHorseAndSpherePosition = () => {
  if (horseLeftRef.value) {
    gsap.set(horseLeftRef.value, { 
      x: 0, y: 0, rotation: 0, scale: 1,
      clearProps: 'transform' 
    })
  }
  if (horseRightRef.value) {
    gsap.set(horseRightRef.value, { 
      x: 0, y: 0, rotation: 0, scale: 1,
      clearProps: 'transform' 
    })
  }
  if (sphereContainerRef.value) {
    gsap.set(sphereContainerRef.value, { 
      y: -80, scale: 1, // 调整到新的初始位置（与CSS一致）
      clearProps: 'transform' 
    })
  }
}

// ========== 【抽奖逻辑】 ==========
const startDraw = async () => {
  if (!currentPrize.value || currentPrize.value.remaining <= 0) return
  if (isDrawing.value) return

  isDrawing.value = true
  winners.value = []

  // 1. 播放马匹顶球动画（0.5秒）
  startHorseAndSphereAnimation()
  
  // 2. 延迟0.5秒进行抽奖
  setTimeout(async () => {
    // 【关键修复】如果有导入数据，在前端直接抽奖；否则调用后端API
    if (hasImportedData.value && importedUsers.value.length > 0) {
      console.log('【抽奖】使用导入数据进行前端抽奖')
      
      try {
        // 过滤掉已中奖的人员和虚位以待
        const existingWinnerIds = new Set(allWinners.value.map(w => w.userId))
        const candidates = importedUsers.value
          .filter(u => !u.isFake && !existingWinnerIds.has(u.id || u.userId))
        
        if (candidates.length === 0) {
          throw new Error('所有用户都已中奖，没有可抽取的候选者')
        }
        
        const drawCount = Math.min(currentPrize.value.batchSize, candidates.length)
        
        // 随机抽取
        const selected = []
        const shuffled = [...candidates].sort(() => Math.random() - 0.5)
        for (let i = 0; i < drawCount; i++) {
          selected.push(shuffled[i])
        }
        
        // 格式化中奖者数据
        const winners = selected.map(user => ({
          name: user.name || '未知',
          id: user.employeeId || user.id || user.userId,
          userId: user.employeeId || user.id || user.userId,
          employeeId: user.employeeId || ''
        }))
        
        console.log('【抽奖】前端抽奖结果:', winners)
        
        // 更新剩余数量
        currentPrize.value.remaining -= winners.length
        
        // 记录中奖人员
        winners.forEach(winner => {
          allWinners.value.push({
            prize: currentPrize.value.name,
            name: winner.name,
            userId: winner.userId,
            employeeId: winner.employeeId || '',
            drawTime: new Date().toISOString()
          })
        })
        
        // 从importedUsers中移除中奖人员
        const winnerIds = winners.map(w => w.id || w.userId)
        importedUsers.value = importedUsers.value.filter(u => 
          !winnerIds.includes(u.id || u.userId)
        )
        
        // 模拟API响应格式
        const data = {
          success: true,
          winners: winners,
          count: winners.length
        }
        
        // 继续执行后续的显示逻辑
        handleDrawResultFromAPI(data)
        
      } catch (error) {
        console.error('【抽奖】前端抽奖失败:', error)
        alert(`抽奖失败: ${error.message || '未知错误'}`)
        isDrawing.value = false
        stopRotationSmoothly()
      }
    } else {
      // 没有导入数据，使用后端API（WebSocket登录用户）
      console.log('【抽奖】使用后端API（WebSocket登录用户）')
      
      const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
      const hostname = window.location.hostname
      const port = window.location.port === '5173' ? ':8000' : (window.location.port ? ':' + window.location.port : '')
      const apiUrl = `${protocol}//${hostname}${port}/api/draw`

      try {
        // 准备请求参数
        const requestBody = {
          count: currentPrize.value.batchSize,
          prize_name: currentPrize.value.name
        }
        
        console.log('【抽奖API】请求参数:', requestBody)
        console.log('【抽奖API】请求URL:', apiUrl)
        
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })

        console.log('【抽奖API】响应状态:', response.status)
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error('【抽奖API】错误响应:', errorText)
          throw new Error(`抽奖失败: ${response.status} ${errorText}`)
        }

        const data = await response.json()
        console.log('【抽奖API】响应数据:', data)
        
        if (data.success) {
          // 更新剩余数量
          currentPrize.value.remaining -= data.count
          
          // 记录中奖人员
          data.winners.forEach(winner => {
            allWinners.value.push({
              prize: currentPrize.value.name,
              name: winner.name || winner.userName || '未知',
              userId: winner.id || winner.userId || `user_${Date.now()}_${Math.random()}`,
              employeeId: winner.employeeId || winner.employee_id || '',
              drawTime: new Date().toISOString()
            })
          })
          
          // 从connectedUsers中移除中奖人员
          const winnerIds = data.winners.map(w => w.id || w.userId)
          connectedUsers.value = connectedUsers.value.filter(u => 
            !winnerIds.includes(u.id || u.userId)
          )
          
          // 继续执行后续的显示逻辑
          handleDrawResultFromAPI(data)
        }
      } catch (error) {
        console.error('【抽奖API】抽奖失败:', error)
        alert(`抽奖失败: ${error.message || '未知错误'}`)
        isDrawing.value = false
        
        // 停止动画
        if (fastRotationAnim) {
          fastRotationAnim.kill()
          fastRotationAnim = null
        }
        if (fastRotationXAnim) {
          fastRotationXAnim.kill()
          fastRotationXAnim = null
        }
        stopRotationSmoothly()
      }
    }
  }, 500) // 延迟0.5秒
}

// ========== 【处理抽奖结果（API响应）】 ==========
const handleDrawResultFromAPI = (data) => {
  // 2.5秒后开始减速（总共3秒快速旋转）
  setTimeout(() => {
    stopRotationSmoothly()
  }, 2500)
  
  // 5秒后显示结果（总共约5.5秒：0.5动画+0.5延迟+3旋转+1.5减速）
  setTimeout(() => {
    isDrawing.value = false
    winners.value = data.winners.map(w => ({
      name: w.name || w.userName || '未知',
      employeeId: w.employeeId || w.employee_id || w.id || '',
      userId: w.userId || w.id || `user_${Date.now()}_${Math.random()}`,
      id: w.employeeId || w.employee_id || w.id || ''
    }))
    
    // 隐藏马匹和球体
    hideHorseAndSphere()
    
    // 撒花
    confetti({
      particleCount: 200,
      spread: 90,
      origin: {y: 0.5},
      colors: ['#FFD700', '#FFA500', '#FF6347', '#FF1493']
    })
    
    // 15秒后自动关闭（可选，主要靠用户点击）
    setTimeout(() => {
      if (winners.value.length > 0) {
        handleResetWinners()
      }
    }, 15000)
  }, 5000) // 总共5秒
}

// ========== 【马匹和球体同步动画 - 改进版】 ==========
const startHorseAndSphereAnimation = () => {
  gsap.killTweensOf([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value])

  // 1. 马匹先向上快速跳跃，做出"顶起"的动作（0.5秒）
  if (horseLeftRef.value) {
    gsap.to(horseLeftRef.value, {
      x: 20, y: -180, rotation: -15, scale: 1.05, // 减小y值（-180而不是-220）
      duration: 0.5, ease: 'back.out(1.7)', force3D: true,
      onComplete: () => {
        // 跳跃后的轻微晃动效果
        gsap.to(horseLeftRef.value, {
          y: '-=8', // 减小晃动幅度
          duration: 0.3,
          yoyo: true,
          repeat: 1,
          ease: 'power2.inOut'
        })
      }
    })
  }

  if (horseRightRef.value) {
    gsap.to(horseRightRef.value, {
      x: -20, y: -180, rotation: 15, scale: 1.05, // 减小y值（-180而不是-220）
      duration: 0.5, ease: 'back.out(1.7)', force3D: true,
      onComplete: () => {
        // 跳跃后的轻微晃动效果
        gsap.to(horseRightRef.value, {
          y: '-=8', // 减小晃动幅度
          duration: 0.3,
          yoyo: true,
          repeat: 1,
          ease: 'power2.inOut'
        })
      }
    })
  }

  // 2. 球体被马匹顶起：先向上快速弹起，然后跟随马匹上升
  if (sphereContainerRef.value) {
    // 第一阶段：被顶起的弹跳效果
    gsap.to(sphereContainerRef.value, {
      y: -150, scale: 1.2, // 减小y值（-150而不是-200）
      duration: 0.5,
      ease: 'back.out(2)',
      onComplete: () => {
        // 第二阶段：跟随马匹上升并轻微抖动
        gsap.to(sphereContainerRef.value, {
          y: -130, // 减小y值（-130而不是-180）
          duration: 0.8,
          ease: 'power2.out',
          onUpdate: function() {
            // 添加轻微抖动效果，模拟被顶起后的不稳定
            const shake = Math.sin(Date.now() * 0.02) * 2
            sphereContainerRef.value.style.transform = `translateY(${parseFloat(this.targets()[0].gsap.y)}px) scale(1.15) translateX(${shake}px)`
          }
        })
      }
    })
    
    // 球体自身旋转加速（配合顶起效果）
    if (sphereWrapperRef.value) {
      const currentRotation = gsap.getProperty(sphereWrapperRef.value, "rotationY") || 0
      gsap.to(sphereWrapperRef.value, {
        rotationY: currentRotation + 180, // 快速旋转半圈
        duration: 0.3,
        ease: 'power3.out',
        onComplete: () => {
          // 然后进入疯狂旋转模式
          startFastRotation()
        }
      })
    }
  }
}

// ========== 【隐藏马匹和球体】 ==========
const hideHorseAndSphere = () => {
  gsap.to([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value], {
    opacity: 0,
    duration: 0.8,
    ease: 'power2.out',
    onComplete: () => {
      // 完全停止旋转
      stopDynamicDepthUpdate()
      if (fastRotationAnim) fastRotationAnim.kill()
      if (fastRotationXAnim) fastRotationXAnim.kill()
      if (sphereRotationAnim) sphereRotationAnim.kill()
    }
  })
}

// ========== 【显示马匹和球体】 ==========
const showHorseAndSphere = () => {
  gsap.to([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value], {
    opacity: 1,
    duration: 0.8,
    ease: 'power2.out'
  })
}

// ========== 【全局点击事件 - 点击任意位置重置】 ==========
const handleGlobalClick = (e) => {
  // 如果点击的是中奖卡片区域，不处理（让卡片本身可以点击）
  if (e.target.closest('.winners-grid-container')) {
    return
  }
  
  // 如果点击的是设置按钮，不处理
  if (e.target.closest('button[title="设置"]')) {
    return
  }
  
  // 如果点击的是导出按钮，不处理
  if (e.target.closest('button[title="导出中奖名单"]')) {
    return
  }
  
  // 如果显示中奖结果，点击空白处重置
  if (winners.value.length > 0) {
    handleResetWinners()
  }
}

// ========== 【重置中奖结果】 ==========
const handleResetWinners = () => {
  winners.value = []
  isDrawing.value = false
  
  // 重置马匹和球体位置
  resetHorseAndSpherePosition()
  
  // 显示马匹和球体
  showHorseAndSphere()
  
  // 如果还有剩余，保持在lottery模式，恢复球体旋转
  if (currentPrize.value && currentPrize.value.remaining > 0) {
    viewMode.value = 'lottery'
    setTimeout(() => {
      updateDisplayUsers()
      startIdleRotation()
    }, 300)
  } else {
    // 如果抽完了，回到home模式
    viewMode.value = 'home'
    currentPrize.value = null
  }
}

// ========== 【键盘事件】 ==========
const handleKeyPress = (e) => {
  if (e.code === 'Space') {
    e.preventDefault()
    if (viewMode.value === 'home') {
      // Home模式，不做任何事
      return
    } else if (winners.value.length > 0) {
      // 关闭结果展示，回到准备模式
      handleResetWinners()
    } else if (!isDrawing.value) {
      // 开始抽奖
      startDraw()
    }
  }
}

// ========== 【3D 球体逻辑】 ==========
const updateDisplayUsers = () => {
  if (viewMode.value !== 'lottery') return
  
  // 【关键修复】优先使用导入数据，如果没有导入数据才使用WebSocket登录数据
  const sourceUsers = hasImportedData.value ? importedUsers.value : connectedUsers.value
  
  // 1️⃣ 统一用户对象格式 - normalize数据，并过滤已中奖人员
  const existingWinnerIds = new Set(allWinners.value.map(w => w.userId))
  let displayList = sourceUsers
    .filter(u => !existingWinnerIds.has(u.id || u.userId)) // 过滤已中奖人员
    .map(u => ({
      userId: u.id || u.userId || `user_${Date.now()}_${Math.random()}`,
      name: u.name || '未知',
      employeeId: u.employeeId || u.employee_id || '',
      isFake: u.isFake || false
    }))
  
  // 2️⃣ 如果少于50人，补齐假数据
  const minCount = 50
  if (displayList.length < minCount) {
    const needFake = minCount - displayList.length
    for(let i=0; i<needFake; i++) {
      displayList.push({ 
        userId: `fake_${i}`,
        name: '虚位以待', 
        employeeId: '',
        isFake: true 
      })
    }
  }
  
  renderSphere(displayList)
}

// ========== 【打开导入模态框】 ==========
const handleOpenImportModal = () => {
  console.log('【Screen】点击导入按钮，打开导入模态框')
  console.log('【Screen】当前 showImportModal 值:', showImportModal.value)
  showImportModal.value = true
  console.log('【Screen】设置 showImportModal 为 true，新值:', showImportModal.value)
}

// ========== 【导入用户数据】 ==========
const importUsersData = (users) => {
  console.log('【Screen】========== 收到导入数据 ==========')
  console.log('【Screen】收到导入数据:', users)
  console.log('【Screen】数据类型:', typeof users)
  console.log('【Screen】是否为数组:', Array.isArray(users))
  console.log('【Screen】数据数量:', users?.length || 0)
  
  if (!users) {
    console.error('【Screen】❌ 数据为 null 或 undefined')
    alert('导入失败：没有收到数据')
    return
  }
  
  if (!Array.isArray(users)) {
    console.error('【Screen】❌ 数据不是数组，类型:', typeof users)
    alert('导入失败：数据格式不正确（不是数组）')
    return
  }
  
  if (users.length === 0) {
    console.error('【Screen】❌ 数据数组为空')
    alert('导入失败：数据为空')
    return
  }
  
  try {
    // 验证和清理数据
    console.log('【Screen】开始验证数据...')
    const validUsers = users.filter((user, index) => {
      if (!user || typeof user !== 'object') {
        console.warn(`【Screen】跳过无效用户 #${index}:`, user)
        return false
      }
      if (!user.name || typeof user.name !== 'string' || !user.name.trim()) {
        console.warn(`【Screen】跳过无姓名用户 #${index}:`, user)
        return false
      }
      return true
    })
    
    console.log('【Screen】验证后有效用户数量:', validUsers.length)
    
    if (validUsers.length === 0) {
      alert('导入失败：没有有效的用户数据（至少需要姓名）')
      return
    }
    
    // 保留现有的WebSocket用户，只添加新导入的用户
    const existingUserIds = new Set(connectedUsers.value
      .filter(u => !u.isFake) // 只检查真实用户
      .map(u => u.id || u.employeeId || u.userId || u.name))
    
    console.log('【Screen】现有用户ID集合:', Array.from(existingUserIds))
    
    const newUsers = validUsers.filter(user => {
      const userId = user.employeeId || user.id || user.userId || user.name
      const isDuplicate = existingUserIds.has(userId)
      if (isDuplicate) {
        console.log('【Screen】跳过重复用户:', user.name, 'ID:', userId)
      }
      return !isDuplicate
    })
    
    console.log('【Screen】去重后新用户数量:', newUsers.length)
    
    if (newUsers.length === 0) {
      alert('导入失败：所有用户都已存在')
      return
    }
    
    // 格式化新用户数据
    const formattedNewUsers = newUsers.map((user, index) => ({
      name: String(user.name || '').trim(),
      id: user.employeeId || user.id || user.userId || `real_${Date.now()}_${index}`,
      userId: user.employeeId || user.id || user.userId || `real_${Date.now()}_${index}`,
      employeeId: String(user.employeeId || user.id || user.userId || '').trim(),
      isFake: false
    }))
    
    console.log('【Screen】格式化后的新用户:', formattedNewUsers.slice(0, 3))
    console.log('【Screen】导入的真实用户数量:', formattedNewUsers.length)
    
    // 【关键修复】将导入的数据存储到独立的 importedUsers 列表
    // 如果导入的数据足够（>=50人），直接用导入的数据，不添加"虚位以待"
    // 如果导入的数据少于50人，才补齐"虚位以待"
    const minCount = 50
    
    if (formattedNewUsers.length >= minCount) {
      // 导入的数据足够，直接用导入的数据，不添加"虚位以待"
      importedUsers.value = formattedNewUsers
      console.log('【Screen】导入数据足够，直接用导入的数据（不添加虚位以待）')
    } else {
      // 导入的数据不足，补齐"虚位以待"
      importedUsers.value = [...formattedNewUsers]
      const needFake = minCount - formattedNewUsers.length
      console.log('【Screen】导入数据不足，需要补齐假数据:', needFake, '个')
      
      // 添加新的假数据
      for(let i=0; i<needFake; i++) {
        importedUsers.value.push({ 
          name: '虚位以待', 
          id: `fake_${Date.now()}_${i}`,
          userId: `fake_${Date.now()}_${i}`,
          employeeId: '',
          isFake: true 
        })
      }
    }
    
    // 标记已导入数据
    hasImportedData.value = true
    
    console.log('【Screen】最终总用户数:', importedUsers.value.length)
    console.log('【Screen】真实用户数:', importedUsers.value.filter(u => !u.isFake).length)
    console.log('【Screen】虚拟用户数:', importedUsers.value.filter(u => u.isFake).length)
    
    // 更新在线人数显示（显示导入的真实用户数）
    const finalRealUserCount = importedUsers.value.filter(u => !u.isFake).length
    userCount.value = finalRealUserCount
    console.log('【Screen】更新在线人数（导入数据）:', finalRealUserCount)
    
    // 强制更新球体显示（无论当前模式）
    console.log('【Screen】当前模式:', viewMode.value)
    console.log('【Screen】强制更新球体显示...')
    
    // 如果不在lottery模式，先切换到lottery模式
    if (viewMode.value !== 'lottery') {
      console.log('【Screen】不在lottery模式，先切换到lottery模式')
      // 可以选择一个默认奖项，或者只是更新显示
      // 这里我们只更新显示，不切换模式
    }
    
    // 立即更新显示 - 确保数据出现在奖池中
    nextTick(() => {
      // 如果不在lottery模式，先切换到lottery模式以显示球体
      if (viewMode.value !== 'lottery') {
        console.log('【Screen】不在lottery模式，切换到lottery模式以显示奖池')
        // 如果有可用奖项，选择第一个
        const availablePrize = prizes.value.find(p => p.remaining > 0)
        if (availablePrize) {
          selectPrize(availablePrize)
        } else {
          // 如果没有可用奖项，直接切换到lottery模式
          viewMode.value = 'lottery'
          resetHorseAndSpherePosition()
          nextTick(() => {
            updateDisplayUsers()
            setTimeout(() => {
              startIdleRotation()
            }, 300)
          })
        }
      } else {
        // 已经在lottery模式，直接更新显示
        updateDisplayUsers()
        console.log('【Screen】球体显示已更新')
        
        // 重新启动旋转
        setTimeout(() => {
          startIdleRotation()
          console.log('【Screen】球体旋转已启动')
        }, 300)
      }
    })
    
    // 通过WebSocket发送用户数据到后端（可选）
    if (ws && ws.readyState === WebSocket.OPEN) {
      console.log('【Screen】通过WebSocket发送用户数据到后端')
      try {
        ws.send(JSON.stringify({
          type: 'add_users',
          users: formattedNewUsers.map(u => ({
            name: u.name,
            id: u.employeeId || u.id,
            employeeId: u.employeeId || ''
          }))
        }))
      } catch (error) {
        console.error('【Screen】WebSocket发送失败:', error)
      }
    } else {
      console.warn('【Screen】WebSocket未连接，跳过同步')
    }
    
    const fakeCount = importedUsers.value.length - finalRealUserCount
    
    // 显示成功提示（模态框形式，带确定按钮）
    showSuccessMessage(`成功导入 ${newUsers.length} 名员工！\n已替换奖池中的"虚位以待"卡片。\n当前奖池总人数: ${importedUsers.value.length}（真实: ${finalRealUserCount}，虚拟: ${fakeCount}）\n\n将使用导入数据进行抽奖。`)
    
    console.log('【Screen】========== 导入完成 ==========')
    console.log('【Screen】当前奖池总人数:', importedUsers.value.length)
    console.log('【Screen】真实用户数:', finalRealUserCount)
    console.log('【Screen】虚拟用户数:', fakeCount)
    console.log('【Screen】已标记使用导入数据进行抽奖')
  } catch (error) {
    console.error('【Screen】❌ 导入失败:', error)
    console.error('【Screen】错误堆栈:', error.stack)
    alert(`导入失败: ${error.message || '未知错误'}\n\n请查看控制台获取详细信息。`)
  }
}

// ========== 【显示成功提示】 ==========
const showSuccessMessage = (message) => {
  successMessage.value = message
  showSuccessToast.value = true
  // 不再自动关闭，需要用户点击确定按钮
}

// ========== 【测试导入功能】 ==========
const testImportUsers = () => {
  console.log('【测试导入】开始测试导入功能')
  const testUsers = [
    { name: '测试用户1', employeeId: 'TEST001', isFake: false },
    { name: '测试用户2', employeeId: 'TEST002', isFake: false },
    { name: '测试用户3', employeeId: 'TEST003', isFake: false },
    { name: '测试用户4', employeeId: 'TEST004', isFake: false },
    { name: '测试用户5', employeeId: 'TEST005', isFake: false }
  ]
  importUsersData(testUsers)
}

// ========== 【导出Excel功能】 ==========
const exportWinnersToExcel = () => {
  if (allWinners.value.length === 0) {
    alert('暂无中奖数据可导出')
    return
  }
  
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
  const hostname = window.location.hostname
  const port = window.location.port === '5173' ? ':8000' : (window.location.port ? ':' + window.location.port : '')
  const exportUrl = `${protocol}//${hostname}${port}/api/export_winners`
  
  // 创建下载链接
  const link = document.createElement('a')
  link.href = exportUrl
  link.download = `中奖名单_${new Date().toISOString().split('T')[0]}.xlsx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
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
    console.warn('sphereWrapperRef 未就绪，等待...')
    setTimeout(() => renderSphere(users), 100)
    return
  }
  
  console.log(`开始渲染 ${users.length} 个用户到球体`)
  
  if (isDrawing.value) return
  
  sphereWrapperRef.value.innerHTML = ''
  
  // 确保有足够的数据
  const displayUsers = users.length > 0 ? users : [...connectedUsers.value]

  displayUsers.forEach((user, i) => {
    // 1. 使用改进的斐波那契球算法获取均匀分布
    const goldenAngle = Math.PI * (3 - Math.sqrt(5)) // 黄金角度
    const theta = goldenAngle * i // 方位角
    const y = 1 - (2 * i) / (displayUsers.length - 1) // y坐标从1到-1
    const radiusAtY = Math.sqrt(1 - y * y) // 在当前y高度的圆半径
    
    const x = SPHERE_RADIUS * radiusAtY * Math.cos(theta)
    const yPos = SPHERE_RADIUS * y
    const z = SPHERE_RADIUS * radiusAtY * Math.sin(theta)
    
    // 2. 计算卡片的朝向（应该正对观察者）
    // 计算法线方向（从球心指向卡片位置）
    const distance = Math.sqrt(x*x + yPos*yPos + z*z)
    const normalX = x / distance
    const normalY = yPos / distance
    const normalZ = z / distance
    
    // 3. 根据法线计算卡片应该旋转的角度
    // 首先计算卡片应该朝向哪个方向（让卡片正对观察者）
    // 计算卡片应该绕Y轴旋转的角度（水平方向）
    const rotateY = -Math.atan2(z, x) * (180 / Math.PI)
    // 计算卡片应该绕X轴旋转的角度（垂直方向）
    const rotateX = Math.asin(normalY) * (180 / Math.PI)
    
    // 4. 创建卡片元素
    const el = document.createElement('div')
    el.className = 'user-card-3d'
    
    if (user.isFake) {
      el.classList.add('user-card-fake')
    }
    
    // 只显示名字和工号
    const nameEl = document.createElement('div')
    nameEl.className = 'name'
    nameEl.textContent = user.name || '未知'
    el.appendChild(nameEl)
    
    if (!user.isFake && user.employeeId) {
      const idEl = document.createElement('div')
      idEl.className = 'id'
      idEl.textContent = user.employeeId
      el.appendChild(idEl)
    }
    
    // 存储用户数据
    el.setAttribute('data-user-id', user.userId)
    el.setAttribute('data-user-name', user.name)
    
    // 5. 设置卡片的初始位置和旋转
    el.style.position = 'absolute'
    el.style.left = '50%'
    el.style.top = '50%'
    el.style.transformOrigin = 'center center'
    el.style.marginLeft = '-70px'
    el.style.marginTop = '-22px'
    
    // 6. 关键：应用位置和朝向
    // 先平移到球面位置，然后旋转卡片使其正对观察者
    el.style.transform = `translate3d(${x}px, ${yPos}px, ${z}px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`
    
    // 7. 存储初始位置和朝向数据用于深度更新
    el.setAttribute('data-initial-x', x.toString())
    el.setAttribute('data-initial-y', yPos.toString())
    el.setAttribute('data-initial-z', z.toString())
    el.setAttribute('data-rotate-y', rotateY.toString())
    el.setAttribute('data-rotate-x', rotateX.toString())
    el.setAttribute('data-depth', '0.5')
    
    sphereWrapperRef.value.appendChild(el)
  })
  
  console.log(`已渲染 ${displayUsers.length} 个3D卡片`)
  
  // 启动动态深度更新
  startDynamicDepthUpdate()
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

  // 设置初始旋转角度，让球体更有立体感
  gsap.set(sphereWrapperRef.value, {
    rotationY: 45, // 初始Y轴旋转45度，让球体有更好的侧面视角
    rotationX: 10, // 初始X轴旋转10度，稍微仰视
  })

  // 创建新的旋转动画
  sphereRotationAnim = gsap.to(sphereWrapperRef.value, {
    rotationY: 360 + 45, // 从45度旋转到405度
    rotationX: 10, // 保持仰角不变
    duration: 25, // 稍微放慢速度
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
  
  // 5. X轴混乱翻滚 - 小幅度正弦摆动（制造混沌，但保持小角度）
  const currentRotationX = gsap.getProperty(sphereWrapperRef.value, "rotationX") || 10
  // 限制摆动范围在 5度到 15度之间，保持仰视角度
  const targetX = Math.max(5, Math.min(15, currentRotationX + gsap.utils.random(-3, 3)))
  
  fastRotationXAnim = gsap.fromTo(sphereWrapperRef.value,
    {
      rotationX: currentRotationX
    },
    {
      rotationX: targetX,
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
      // 统一数据格式
      winners.value = msg.winners.map(w => ({
        name: w.name || w.userName || '未知',
        employeeId: w.employeeId || w.employee_id || '',
        userId: w.userId || w.id || `user_${Date.now()}_${Math.random()}`,
        id: w.employeeId || w.employee_id || w.id || ''
      }))
      
      // 记录中奖人员
      msg.winners.forEach(winner => {
        allWinners.value.push({
          prize: currentPrize.value?.name || '未知奖项',
          name: winner.name || winner.userName || '未知',
          userId: winner.id || winner.userId || `user_${Date.now()}_${Math.random()}`,
          employeeId: winner.employeeId || winner.employee_id || '',
          drawTime: new Date().toISOString()
        })
      })
      
      // 隐藏马匹和球体
      hideHorseAndSphere()
      
      // 撒花
      confetti({
        particleCount: 200,
        spread: 90,
        origin: {y: 0.5},
        colors: ['#FFD700', '#FFA500', '#FF6347', '#FF1493']
      })
      // 30秒后自动关闭（可选，主要靠用户点击）
      setTimeout(() => {
        if (winners.value.length > 0) {
          handleResetWinners()
        }
      }, 30000) // 30秒自动关闭
    }, 2000) // 等待2秒减速完成
  }
}

// 平滑停止旋转的独立函数
const stopRotationSmoothly = () => {
  if (!sphereWrapperRef.value) return
  
  // 0. 停止动态深度更新
  stopDynamicDepthUpdate()
  
  // 1. 移除快速旋转类名
  if (sphereWrapperRef.value) {
    sphereWrapperRef.value.classList.remove('sphere-active')
  }
  
  // 2. 马匹先停止并稍微下降，模拟接住球体的感觉
  if (horseLeftRef.value) {
    gsap.to(horseLeftRef.value, {
      y: -140, // 减小y值（-140而不是-180）
      duration: 1.2,
      ease: "power2.out"
    })
  }
  
  if (horseRightRef.value) {
    gsap.to(horseRightRef.value, {
      y: -140, // 减小y值（-140而不是-180）
      duration: 1.2,
      ease: "power2.out"
    })
  }
  
  // 3. 先停止X轴摆动，再减速Y轴
  const currentX = gsap.getProperty(sphereWrapperRef.value, "rotationX") || -5
  if (fastRotationXAnim) {
    fastRotationXAnim.kill()
    fastRotationXAnim = null
  }
  gsap.to(sphereWrapperRef.value, {
    rotationX: 10, // 回正到稍微仰视的角度，增强立体感
    duration: 1.2,
    ease: "power2.out",
    force3D: true
  })
  
  // 4. 获取当前Y轴旋转角度并平滑减速
  const currentRotationY = gsap.getProperty(sphereWrapperRef.value, "rotationY") || 0
  
  // 5. Kill Y轴旋转动画
  if (fastRotationAnim) {
    fastRotationAnim.kill()
    fastRotationAnim = null
  }
  
  // 6. 平滑减速Y轴旋转，同时球体缓缓下降（1.5秒）
  gsap.to(sphereWrapperRef.value, {
    rotationY: currentRotationY, // 保持当前角度，停止旋转
    duration: 1.5,
    ease: "power2.out",
    force3D: true
  })
  
  // 7. 球体缓缓下降到马匹之间（1.5秒）
  if (sphereContainerRef.value) {
    gsap.to(sphereContainerRef.value, {
      y: -100, // 下降到马匹之间
      scale: 1.05, // 稍微缩小一点
      duration: 1.5,
      ease: "power2.out",
      onComplete: () => {
        // 停止后，恢复所有卡片的正常显示
        const cards = sphereWrapperRef.value.querySelectorAll('.user-card-3d')
        cards.forEach(card => {
          // 移除模糊，恢复正常显示
          gsap.set(card, { opacity: 1, scale: 1, filter: 'blur(0px)' })
        })
      }
    })
  }
  
  console.log('马匹接住球体，球体开始平滑减速并下降')
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
    const sphereRotationY = gsap.getProperty(sphereWrapperRef.value, "rotationY") || 45
    const sphereRotationX = gsap.getProperty(sphereWrapperRef.value, "rotationX") || 10
    
    cards.forEach(card => {
      // 获取卡片的初始球面位置
      const initialX = parseFloat(card.getAttribute('data-initial-x') || '0')
      const initialY = parseFloat(card.getAttribute('data-initial-y') || '0')
      const initialZ = parseFloat(card.getAttribute('data-initial-z') || '0')
      const initialRotateY = parseFloat(card.getAttribute('data-rotate-y') || '0')
      const initialRotateX = parseFloat(card.getAttribute('data-rotate-x') || '0')
      
      // 计算球体旋转后的卡片位置
      // 将球体旋转角度转换为弧度
      const radY = (sphereRotationY * Math.PI) / 180
      const radX = (sphereRotationX * Math.PI) / 180
      
      // 绕Y轴旋转（水平旋转）
      let x = initialX
      let y = initialY
      let z = initialZ
      
      const cosY = Math.cos(radY)
      const sinY = Math.sin(radY)
      const x1 = x * cosY + z * sinY
      const z1 = z * cosY - x * sinY
      x = x1
      z = z1
      
      // 绕X轴旋转（垂直旋转）
      const cosX = Math.cos(radX)
      const sinX = Math.sin(radX)
      const y1 = y * cosX - z * sinX
      const z2 = y * sinX + z * cosX
      y = y1
      z = z2
      
      // 计算卡片在世界坐标系中的新朝向
      // 卡片需要正对观察者，所以需要结合球体旋转和初始朝向
      const finalRotateY = initialRotateY - sphereRotationY
      const finalRotateX = initialRotateX + sphereRotationX
      
      // 根据z坐标计算深度效果
      // z坐标范围：-SPHERE_RADIUS 到 SPHERE_RADIUS
      const normalizedZ = (z + SPHERE_RADIUS) / (2 * SPHERE_RADIUS) // 0到1
      
      // 【增强立体感】更明显的深度效果 - 增强对比度
      const depthOpacity = 0.1 + normalizedZ * 0.9 // 背面0.1，正面1.0（增强对比）
      const depthScale = 0.3 + normalizedZ * 0.7 // 背面0.3，正面1.0（增强大小对比）
      const depthBlur = (1 - normalizedZ) * 10 // 背面模糊10px，正面不模糊（增强模糊对比）
      
      // 应用新的变换
      // 关键：先平移到旋转后的位置，然后旋转卡片使其正对观察者
      card.style.transform = `translate3d(${x}px, ${y}px, ${z}px) rotateY(${finalRotateY}deg) rotateX(${finalRotateX}deg) scale(${depthScale})`
      
      // 更新样式
      card.style.opacity = depthOpacity.toString()
      card.style.filter = `blur(${depthBlur}px)`
      
      // 更新深度数据
      card.setAttribute('data-depth', normalizedZ.toFixed(3))
      
      // 根据深度调整发光效果（增强立体感）
      if (normalizedZ > 0.7) {
        // 正面卡片：强烈发光
        card.style.borderWidth = '3px'
        card.style.boxShadow = '0 0 30px rgba(255, 215, 0, 0.9), 0 0 50px rgba(255, 215, 0, 0.6)'
      } else if (normalizedZ < 0.3) {
        // 背面卡片：弱发光
        card.style.borderWidth = '1px'
        card.style.boxShadow = '0 0 10px rgba(255, 215, 0, 0.2)'
      } else {
        // 中间卡片：中等发光
        card.style.borderWidth = '2px'
        card.style.boxShadow = '0 0 20px rgba(255, 215, 0, 0.5)'
      }
    })
    
    animationFrameId = requestAnimationFrame(updateDepth)
  }
  
  animationFrameId = requestAnimationFrame(updateDepth)
  depthUpdateInterval = animationFrameId
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

/* ========== 【右侧奖项控制栏样式】垂直排列 ========== */
.prize-sidebar-container {
  display: flex;
  flex-direction: column;
  min-width: 140px;
}

.prize-sidebar-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 120px;
  transition: all 0.2s ease;
  text-align: center;
}

.prize-sidebar-button:not(:disabled):hover {
  transform: translateX(-4px);
}

/* ========== 【3D 舞台容器 - 透视必须来自父级舞台】 ========== */
.scene-stage {
  position: relative;
  width: 100%;
  height: 100%;
  perspective: 2500px !important; /* 增大透视值，增强3D立体效果 */
  perspective-origin: center center; /* 透视原点 */
  display: flex; /* 强制flex布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  transform-style: preserve-3d; /* 确保3D变换传递 */
}

/* ========== 【马匹样式】 ========== */
.horse-wrapper {
  position: absolute;
  top: calc(50% + 290px); /* 增加这个值，让马匹在更下方 */
  width: 240px; /* 稍微缩小马匹 */
  height: auto;
  will-change: transform;
  transform: translateY(-50%);
  pointer-events: none;
  z-index: 15; /* 确保在马匹层 */
}

.horse-left {
  left: calc(50% - 300px); /* 向左移动更多，离中心更远 */
}

.horse-right {
  right: calc(50% - 300px); /* 向右移动更多，离中心更远 */
}

.horse-img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
  opacity: 0.9; /* 提高透明度，使其更明显 */
  mix-blend-mode: screen !important;
  filter: contrast(1.6) brightness(1.3) drop-shadow(0 0 20px rgba(245, 158, 11, 0.7));
  mask-image: radial-gradient(closest-side, black 40%, transparent 100%);
  -webkit-mask-image: radial-gradient(closest-side, black 40%, transparent 100%);
  mask-size: cover;
  -webkit-mask-size: cover;
  mask-position: center;
  -webkit-mask-position: center;
  pointer-events: none;
}

/* ========== 【球体容器 - 负责定位和透视】 ========== */
.sphere-container {
  position: relative;
  width: 600px; /* 增大容器，给3D效果更多空间 */
  height: 600px;
  z-index: 20; /* 确保在马匹上方 */
  transform: translateY(-80px); /* 增加这个负值，让球体更高 */
  perspective: 2500px !important; /* 增大透视值，增强3D立体感 */
  perspective-origin: center center;
  transform-style: preserve-3d !important;
}

/* ========== 【3D旋转容器 - 负责旋转和承载卡片】 ========== */
.sphere-wrapper {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform: translate(-50%, -50%); /* 居中，不后移，让球体在Z=0平面 */
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
  -webkit-transform-style: preserve-3d !important;
  /* 金色光芒效果 - 旋转时隐隐发光，增强效果 */
  filter: drop-shadow(0 0 40px rgba(245, 158, 11, 0.6)) 
          drop-shadow(0 0 70px rgba(250, 204, 21, 0.5))
          drop-shadow(0 0 100px rgba(245, 158, 11, 0.4))
          drop-shadow(0 0 130px rgba(250, 204, 21, 0.3));
}

/* ========== 【Active 状态样式 - 抽奖时强烈的金色光芒效果】 ========== */
.sphere-wrapper.sphere-active {
  /* 抽奖时：强烈的金色光芒效果 */
  filter: drop-shadow(0 0 40px rgba(245, 158, 11, 0.8)) 
          drop-shadow(0 0 60px rgba(250, 204, 21, 0.7))
          drop-shadow(0 0 100px rgba(245, 158, 11, 0.6))
          drop-shadow(0 0 140px rgba(250, 204, 21, 0.5))
          drop-shadow(0 0 180px rgba(245, 158, 11, 0.4));
  /* 添加呼吸动画，让光芒闪烁 */
  animation: goldenGlow 1.2s ease-in-out infinite;
}

/* ========== 【金色光芒呼吸动画】 ========== */
@keyframes goldenGlow {
  0%, 100% {
    filter: drop-shadow(0 0 50px rgba(245, 158, 11, 0.9)) 
            drop-shadow(0 0 80px rgba(250, 204, 21, 0.8))
            drop-shadow(0 0 120px rgba(245, 158, 11, 0.7))
            drop-shadow(0 0 160px rgba(250, 204, 21, 0.6))
            drop-shadow(0 0 200px rgba(245, 158, 11, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 60px rgba(245, 158, 11, 1)) 
            drop-shadow(0 0 100px rgba(250, 204, 21, 0.9))
            drop-shadow(0 0 140px rgba(245, 158, 11, 0.8))
            drop-shadow(0 0 180px rgba(250, 204, 21, 0.7))
            drop-shadow(0 0 220px rgba(245, 158, 11, 0.6));
  }
}

/* ========== 【马匹顶起时的发光效果】 ========== */
.horse-wrapper.horse-active .horse-img {
  animation: horseGlow 0.8s ease-in-out infinite;
}

@keyframes horseGlow {
  0%, 100% {
    filter: contrast(1.6) brightness(1.3) drop-shadow(0 0 20px rgba(245, 158, 11, 0.7));
  }
  50% {
    filter: contrast(1.8) brightness(1.5) drop-shadow(0 0 35px rgba(245, 158, 11, 1));
  }
}

/* ========== 【球体被顶起时的弹性动画】 ========== */
@keyframes sphereBounce {
  0% {
    transform: translateY(-40px) scale(1);
  }
  30% {
    transform: translateY(-220px) scale(1.25);
  }
  50% {
    transform: translateY(-200px) scale(1.2);
  }
  70% {
    transform: translateY(-210px) scale(1.22);
  }
  100% {
    transform: translateY(-180px) scale(1.15);
  }
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

/* ========== 【3D 卡片样式 - 已移至非 scoped 样式块，用于动态生成的元素】 ========== */

/* ========== 【批量中奖展示】 ========== */
.winners-grid-container {
  width: 90%;
  max-width: 1200px;
}

.single-winner {
  text-align: center;
  /* 单人展示容器样式 */
  padding: 40px;
}

.winners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  padding: 40px;
  max-width: 100%;
}

/* 针对10人中奖的情况，优化布局 */
@media (min-width: 1200px) {
  .winners-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1199px) and (min-width: 800px) {
  .winners-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 799px) {
  .winners-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 20px;
  }
}

.winner-card {
  /* 深黑底、粗金边、强烈光晕 */
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(12px);
  border: 4px solid #FFD700;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 0 50px rgba(255, 215, 0, 0.6),
              0 10px 30px rgba(0, 0, 0, 0.8),
              inset 0 0 20px rgba(255, 215, 0, 0.1);
  animation: popIn 0.5s ease-out;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.winner-card:hover {
  transform: scale(1.05);
  box-shadow: 0 0 60px rgba(255, 215, 0, 0.8),
              0 10px 30px rgba(0, 0, 0, 0.8),
              inset 0 0 20px rgba(255, 215, 0, 0.2);
}

.winner-card-name {
  font-size: 28px;
  font-weight: 800;
  /* 亮金色纹理，配合黑色描边 */
  color: #FACC15;
  text-shadow: 0 2px 0 black,
               0 0 10px rgba(250, 204, 21, 0.8),
               0 0 20px rgba(250, 204, 21, 0.6),
               0 0 30px rgba(250, 204, 21, 0.4);
  margin-bottom: 8px;
}

.winner-card-id {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.winner-badge {
  display: inline-block;
  background: linear-gradient(to right, #dc2626, #991b1b);
  border: 4px solid #FFD700;
  color: white;
  padding: 8px 30px;
  border-radius: 50px;
  font-size: 24px;
  font-weight: bold;
  box-shadow: 0 0 50px rgba(255, 215, 0, 0.6),
              0 10px 20px rgba(0, 0, 0, 0.5);
  margin-bottom: 20px;
}

.winner-name {
  font-size: 120px;
  font-weight: 900;
  text-transform: uppercase;
  /* 亮金色纹理，配合黑色描边 - 极度醒目 */
  color: #FACC15;
  text-shadow: 0 2px 0 black,
               0 4px 0 rgba(0, 0, 0, 0.8),
               0 0 20px rgba(250, 204, 21, 1),
               0 0 40px rgba(250, 204, 21, 0.8),
               0 0 60px rgba(250, 204, 21, 0.6),
               0 0 80px rgba(250, 204, 21, 0.4);
  /* 可选：使用渐变背景（如果浏览器支持） */
  background: linear-gradient(to bottom, #FDE68A, #F59E0B, #B45309);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 5px 0 #b45309) drop-shadow(0 20px 40px rgba(0, 0, 0, 0.8));
}

.winner-id {
  font-size: 32px;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 20px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8),
               0 0 10px rgba(255, 255, 255, 0.3);
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

/* 模态框动画 */
.modal-fade-enter-active {
  transition: all 0.3s ease-out;
}

.modal-fade-leave-active {
  transition: all 0.3s ease-in;
}

.modal-fade-enter-from {
  opacity: 0;
}

.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .glass-panel {
  transform: scale(0.9) translateY(-20px);
}

.modal-fade-leave-to .glass-panel {
  transform: scale(0.9) translateY(-20px);
}
</style>

<!-- 非 scoped 样式：用于动态生成的 DOM 元素 -->
<style>
/* ========== 【3D 卡片样式 - 黑金风格（动态生成元素）】 ========== */
.user-card-3d {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 140px;
  min-height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  /* 深黑底，半透明 */
  background: linear-gradient(135deg, 
    rgba(10, 10, 10, 0.95) 0%, 
    rgba(30, 30, 30, 0.85) 50%, 
    rgba(10, 10, 10, 0.95) 100%);
  backdrop-filter: blur(8px);
  /* 亮金边框 - 根据深度动态调整 */
  border: 2px solid #FFD700;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.8),
    0 0 30px rgba(255, 215, 0, 0.6),
    inset 0 0 15px rgba(255, 215, 0, 0.2),
    inset 0 0 30px rgba(0, 0, 0, 0.5);
  transition: transform 0.05s linear, opacity 0.05s linear, filter 0.05s linear;
  /* 3D关键属性 */
  transform-style: preserve-3d !important;
  backface-visibility: visible !important;
  pointer-events: none;
  /* 文字样式 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  /* 确保3D变换正常 */
  -webkit-transform-style: preserve-3d !important;
  -webkit-backface-visibility: visible !important;
  /* 添加微妙的纹理效果 */
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(255, 215, 0, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 215, 0, 0.1) 0%, transparent 50%);
}

.user-card-3d .name {
  font-size: 18px;
  font-weight: 800;
  color: #FFD700;
  text-shadow: 
    0 1px 3px #000,
    0 0 10px rgba(255, 215, 0, 0.7),
    0 0 20px rgba(255, 215, 0, 0.5);
  line-height: 1.2;
  text-align: center;
  width: 100%;
  letter-spacing: 0.5px;
}

.user-card-3d .id {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 
    0 1px 2px rgba(0, 0, 0, 1),
    0 0 5px rgba(255, 255, 255, 0.3);
  line-height: 1.2;
  opacity: 0.9;
  margin-top: 2px;
}

/* ========== 【假数据卡片样式 - 虚位以待】 ========== */
.user-card-3d.user-card-fake {
  background: linear-gradient(
    135deg,
    rgba(30, 30, 30, 0.9) 0%,
    rgba(50, 50, 50, 0.7) 50%,
    rgba(30, 30, 30, 0.9) 100%
  );
  border: 3px solid #F59E0B;
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 1),
    0 0 40px rgba(245, 158, 11, 0.9),
    0 0 60px rgba(245, 158, 11, 0.7),
    inset 0 0 20px rgba(245, 158, 11, 0.3),
    inset 0 0 40px rgba(0, 0, 0, 0.6);
}

.user-card-3d.user-card-fake .name {
  color: #F59E0B;
  font-size: 20px;
  font-weight: 900;
  text-shadow: 
    0 1px 3px #000,
    0 0 15px rgba(245, 158, 11, 1),
    0 0 25px rgba(245, 158, 11, 0.8),
    0 0 35px rgba(245, 158, 11, 0.6);
}

/* ========== 【球体容器样式优化】 ========== */
.sphere-wrapper {
  /* 确保3D效果正常工作 */
  transform-style: preserve-3d !important;
  -webkit-transform-style: preserve-3d !important;
}

/* ========== 【深度效果调节】 ========== */
/* 通过JS动态控制，这里不需要CSS规则 */
</style>
