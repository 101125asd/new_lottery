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

            <!-- 3D 球体容器 - 绑定 ref 用于 GSAP 动画 -->
          <div ref="sphereContainerRef" class="tag-cloud-wrapper">
            <Sphere3D 
              ref="sphere3dRef"
              :entries="tagCloudEntries" 
              :speed="cloudSpeed"
              :layout="'sphere'"
              :config="{
                fontColor: '#FFD700',
                fontSize: '16',
                fontWeight: 'bold'
              }"
            />
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
          <!-- 操作提示 -->
          <div class="mt-8 text-center text-yellow-300 text-lg font-bold animate-pulse">
            点击任意位置或按空格键继续下一轮抽奖
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
  import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { gsap } from 'gsap'
import confetti from 'canvas-confetti'
import QrcodeVue from 'qrcode.vue'
import SettingsModal from './SettingsModal.vue'
  import ImportModal from './ImportModal.vue'
  import Sphere3D from './Sphere3D.vue'
  import * as XLSX from 'xlsx'

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
  const sphereContainerRef = ref(null) // Sphere3D 容器，用于 GSAP 动画
  const sphere3dRef = ref(null) // Sphere3D 组件引用

// ========== 【常量】 ==========
  const MAX_COUNT = 500 // 最大卡片数量，防止DOM太多导致卡顿
  const MIN_DISPLAY_COUNT = 80 // 最小显示数量，保证云标签效果
let ws = null
  // 已删除：sphereRotationAnim, fastRotationAnim, fastRotationXAnim, SPHERE_RADIUS（改用 TagCloud3D 组件）
  
  // ========== 【TagCloud3D 速度控制】 ==========
  const cloudSpeed = ref(0.5) // 待机时慢速

  // ========== 【球体容器位移常量】 ==========
  // tag-cloud-wrapper 在 CSS 中已 translate(-50%, -50%) 居中
  // 这里的 y 是额外的 GSAP 垂直偏移
  const SPHERE_IDLE_Y = -60   // 待机：接近马头位置（降低高度）
  const SPHERE_LIFT_Y = -200  // 顶起：更高，制造悬浮感
  const SPHERE_HOVER_Y = -200 // 顶起后：稍回落，保持悬浮

  // ========== 【TagCloud3D 数据转换】 ==========
  const tagCloudEntries = computed(() => {
    if (viewMode.value !== 'lottery') return []
    
    // 【关键修复】优先使用导入数据，如果没有导入数据才使用WebSocket登录数据
    const sourceUsers = hasImportedData.value ? importedUsers.value : connectedUsers.value
    
    // 1️⃣ 统一用户对象格式 - normalize数据，并过滤已中奖人员
    const existingWinnerIds = new Set(allWinners.value.map(w => w.userId))
    let displayList = sourceUsers
      .filter(u => !existingWinnerIds.has(u.id || u.userId)) // 过滤已中奖人员
      .map(u => ({
        userId: u.id || u.userId || `user_${Date.now()}_${Math.random()}`,
        // 【关键修复】支持多种字段名：name/userName, employeeId/employee_id/ID
        name: u.name || u.userName || '未知',
        employeeId: u.employeeId || u.employee_id || u.ID || '',
        isFake: u.isFake || false
      }))
    
    // 2️⃣ 【核心修复】强制假数据填充：无论有没有真实用户，必须保证至少80个
    const MIN_DISPLAY_COUNT = 80
    if (displayList.length < MIN_DISPLAY_COUNT) {
      const needFake = MIN_DISPLAY_COUNT - displayList.length
      for (let i = 0; i < needFake; i++) {
        displayList.push({
          userId: `fake_${Date.now()}_${i}`,
          name: '虚位以待', 
          employeeId: '',
          isFake: true 
        })
      }
      console.log(`【强制填充】用户数${displayList.length - needFake}，补齐假数据到${MIN_DISPLAY_COUNT}个`)
    }
    
    // 3️⃣ 如果超过500人，只显示前500个
    if (displayList.length > MAX_COUNT) {
      const realUsers = displayList.filter(u => !u.isFake)
      if (realUsers.length > MAX_COUNT) {
        const shuffled = [...realUsers].sort(() => Math.random() - 0.5)
        displayList = shuffled.slice(0, MAX_COUNT)
        console.log(`真实用户${realUsers.length}人超过${MAX_COUNT}，随机选择${MAX_COUNT}个显示`)
      } else {
        // 保留所有真实用户，补充假数据到500
        const needFake = MAX_COUNT - realUsers.length
        const fakeUsers = displayList.filter(u => u.isFake)
        displayList = [...realUsers, ...fakeUsers.slice(0, needFake)]
        console.log(`真实用户${realUsers.length}人，显示${displayList.length}个（含假数据）`)
      }
    }
    
    // 4️⃣ 转换为 TagCloud3D 需要的格式
    return displayList.map(user => {
      // 组合姓名和工号显示
      let label = user.name || '未知'
      if (user.employeeId && !user.isFake) {
        label = `${user.name || '未知'} ${user.employeeId}`
      }
      return {
        label: label,
        url: '#',
        target: '_top'
      }
    })
  })

  // ========== 【初始化】 ==========
  onMounted(() => {
    const origin = window.location.origin
    qrValue.value = `${origin}/mobile`
    initWebSocket()

    // 数据填充兜底：如果没有真实用户，不生成假数据，等待真实用户登录
    // 移除自动生成假数据的逻辑，让球体显示真实的在线用户数量
    nextTick(() => {
      // 不再自动生成假数据，等待真实用户登录或导入数据

      // TagCloud3D 组件会自动根据 tagCloudEntries 渲染，无需手动初始化
  })

  window.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  if (ws) ws.close()
  window.removeEventListener('keydown', handleKeyPress)
    // TagCloud3D 组件会自动清理，无需手动清理动画
})

// ========== 【WebSocket】 ==========
const initWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const hostname = window.location.hostname
  // 【关键修复】前端开发服务器端口（5173, 5174等）应该连接后端服务器端口（8000）
  // 如果是生产环境（没有端口或端口不是开发服务器），使用当前端口
  const currentPort = window.location.port
  const isDevServer = currentPort && (currentPort === '5173' || currentPort === '5174' || currentPort.startsWith('517'))
  const port = isDevServer ? ':8000' : (currentPort ? ':' + currentPort : '')
  const wsUrl = `${protocol}//${hostname}${port}/ws/screen`
  
  console.log('【WebSocket】尝试连接:', wsUrl)
  console.log('【WebSocket】当前端口:', currentPort, '是否开发服务器:', isDevServer)

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
          console.log('【WebSocket】更新 connectedUsers:', connectedUsers.value.length, '人')
          console.log('【WebSocket】用户数据示例:', connectedUsers.value.slice(0, 3))
          // TagCloud3D 会自动响应 tagCloudEntries 的变化，无需手动更新
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
  
    // 重置马匹位置
    resetHorseAndSpherePosition()
    
    // 重置云标签速度
    cloudSpeed.value = 0.5
    
    // 【核心修复】确保DOM已经渲染后再更新显示
    // 使用nextTick再加一个短暂延时，确保Vue已经把DOM挂载到了页面上
  nextTick(() => {
      // 淡入动画
      if (horseLeftRef.value && horseRightRef.value) {
        gsap.fromTo([horseLeftRef.value, horseRightRef.value], 
        { opacity: 0 },
        { opacity: 1, duration: 0.8, ease: 'power2.out' }
      )
    }
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
      // 重置球体容器到初始位置（居中，y: 0）
      gsap.set(sphereContainerRef.value, { 
        y: SPHERE_IDLE_Y, // 初始位置：略高于中心
        scale: 1, // 恢复初始大小
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

    // 1. 加速云标签旋转（极速）
    cloudSpeed.value = 10

    // 2. 播放马匹顶球动画（0.5秒）
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
          // 恢复云标签速度
          cloudSpeed.value = 0.5
        }
      } else {
        // 没有导入数据，使用后端API（WebSocket登录用户）
        console.log('【抽奖】使用后端API（WebSocket登录用户）')

        const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
        const hostname = window.location.hostname
        // 【关键修复】前端开发服务器端口（5173, 5174等）应该连接后端服务器端口（8000）
        const currentPort = window.location.port
        const isDevServer = currentPort && (currentPort === '5173' || currentPort === '5174' || currentPort.startsWith('517'))
        const port = isDevServer ? ':8000' : (currentPort ? ':' + currentPort : '')
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
           
           // 恢复云标签速度
           cloudSpeed.value = 0.5
         }
      }
    }, 500) // 延迟0.5秒
  }

  // ========== 【处理抽奖结果（API响应）】 ==========
  const handleDrawResultFromAPI = (data) => {
    // 2.5秒后开始减速（总共3秒快速旋转）
    setTimeout(() => {
      // 恢复TagCloud3D慢速旋转
      cloudSpeed.value = 0.5
      
      // 球体容器平滑落回原位
      if (sphereContainerRef.value) {
        gsap.to(sphereContainerRef.value, {
          y: SPHERE_IDLE_Y, // 落回待机高度
          scale: 1, // 恢复初始大小
          duration: 1.5,
          ease: 'power2.out'
        })
      }
      
      // 马匹也落回原位
      if (horseLeftRef.value) {
        gsap.to(horseLeftRef.value, {
          y: 0,
          duration: 1.2,
          ease: 'power2.out'
        })
      }
      if (horseRightRef.value) {
        gsap.to(horseRightRef.value, {
          y: 0,
          duration: 1.2,
          ease: 'power2.out'
        })
      }
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

      // 移除自动关闭：等待操作员手动点击屏幕或按空格键才返回
    }, 5000) // 总共5秒
  }

  // ========== 【马匹和球体同步动画 - 修复版】 ==========
  const startHorseAndSphereAnimation = () => {
    gsap.killTweensOf([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value])

    // 1. 马匹向上快速跳跃，做出"顶起"的动作（0.5秒）
    if (horseLeftRef.value) {
      gsap.to(horseLeftRef.value, {
        x: 20, y: -120, rotation: -15, scale: 1.05,
        duration: 0.5, ease: 'back.out(1.7)', force3D: true,
        onComplete: () => {
          // 跳跃后的轻微晃动效果
          gsap.to(horseLeftRef.value, {
            y: '-=5',
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
        x: -20, y: -120, rotation: 15, scale: 1.05,
        duration: 0.5, ease: 'back.out(1.7)', force3D: true,
        onComplete: () => {
          // 跳跃后的轻微晃动效果
          gsap.to(horseRightRef.value, {
            y: '-=5',
            duration: 0.3,
            yoyo: true,
            repeat: 1,
            ease: 'power2.inOut'
          })
        }
      })
    }

    // 2. 球体容器跟随马匹上升，制造被顶起的效果
    if (sphereContainerRef.value) {
      // 第一阶段：被顶起的弹跳效果（与马匹同步）
      gsap.to(sphereContainerRef.value, {
        y: SPHERE_LIFT_Y, // 比马匹更高，制造悬浮感
        scale: 1.1, // 被顶起时稍微变大
        duration: 0.5, // 与马匹动画同步
        ease: 'back.out(1.7)', // 与马匹动画同步
        force3D: true,
        onComplete: () => {
          // 第二阶段：保持悬浮并轻微抖动
          // 关键修复：不要手动覆盖 style.transform（会覆盖 translate(-50%, -50%) 导致位置错乱）
          gsap.to(sphereContainerRef.value, {
            y: SPHERE_HOVER_Y,
            duration: 0.8,
            ease: 'power2.out',
            force3D: true
          })

          // 抖动用 GSAP 的 x 来做，不覆盖 transform
          gsap.to(sphereContainerRef.value, {
            x: 6,
            duration: 0.08,
            yoyo: true,
            repeat: 10,
            ease: 'sine.inOut',
            force3D: true,
            onComplete: () => {
              if (sphereContainerRef.value) gsap.set(sphereContainerRef.value, { x: 0 })
            }
          })
        }
      })
    }
  }

  // ========== 【隐藏马匹和球体】 ==========
  const hideHorseAndSphere = () => {
    gsap.to([horseLeftRef.value, horseRightRef.value, sphereContainerRef.value], {
      opacity: 0,
      duration: 0.8,
      ease: 'power2.out'
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

    // 如果点击的是导入按钮，不处理
    if (e.target.closest('button[title="导入人员名单"]')) {
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

    // 如果还有剩余，保持在lottery模式，恢复云标签速度
    if (currentPrize.value && currentPrize.value.remaining > 0) {
      viewMode.value = 'lottery'
      // 恢复云标签速度
      cloudSpeed.value = 0.5
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

  // ========== 【3D 球体逻辑 - 已删除，改用 TagCloud3D】 ==========
  // updateDisplayUsers 函数已删除，数据转换逻辑已移至 tagCloudEntries computed 属性

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
      // 直接使用导入的数据，不补齐假数据，只有在超过500时才截断
      if (formattedNewUsers.length > MAX_COUNT) {
        // 如果导入的数据超过500人，只保留前500个
        importedUsers.value = formattedNewUsers.slice(0, MAX_COUNT)
        console.log(`【Screen】导入数据${formattedNewUsers.length}人超过${MAX_COUNT}，只保留前${MAX_COUNT}个`)
      } else {
        // 导入的数据不超过500人，直接使用所有数据（不补齐假数据）
        importedUsers.value = formattedNewUsers
        console.log(`【Screen】导入数据${formattedNewUsers.length}人，直接使用（不补齐假数据）`)
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
            // 恢复云标签速度
            cloudSpeed.value = 0.5
          }
        } else {
          // 已经在lottery模式，恢复云标签速度
          cloudSpeed.value = 0.5
          console.log('【Screen】云标签显示已更新')
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

      // 显示成功提示（模态框形式，带确定按钮）
      const fakeCount = importedUsers.value.filter(u => u.isFake).length
      if (fakeCount > 0) {
        showSuccessMessage(`成功导入 ${newUsers.length} 名员工！\n当前奖池总人数: ${importedUsers.value.length}（真实: ${finalRealUserCount}，虚拟: ${fakeCount}）\n\n将使用导入数据进行抽奖。`)
      } else {
        showSuccessMessage(`成功导入 ${newUsers.length} 名员工！\n当前奖池总人数: ${importedUsers.value.length}人\n\n将使用导入数据进行抽奖。`)
      }

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

  // ========== 【导出Excel功能 - 前端生成】 ==========
  const exportWinnersToExcel = () => {
    if (allWinners.value.length === 0) {
      alert('暂无中奖数据可导出')
      return
    }

    console.log('【导出Excel】开始生成Excel文件，中奖数据数量:', allWinners.value.length)

    try {
      // 1. 准备数据：转换为Excel格式
      const excelData = allWinners.value.map(winner => ({
        '奖项': winner.prize || '未知',
        '姓名': winner.name || '未知',
        '工号': winner.employeeId || winner.id || '',
        '抽奖时间': winner.drawTime ? new Date(winner.drawTime).toLocaleString('zh-CN') : ''
      }))

      // 2. 创建工作簿
      const worksheet = XLSX.utils.json_to_sheet(excelData)
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, worksheet, '中奖名单')

      // 3. 设置列宽（可选，提升可读性）
      const colWidths = [
        { wch: 15 }, // 奖项
        { wch: 12 }, // 姓名
        { wch: 15 }, // 工号
        { wch: 20 }  // 抽奖时间
      ]
      worksheet['!cols'] = colWidths

      // 4. 生成Excel文件并下载
      const fileName = `中奖名单_${new Date().toISOString().split('T')[0]}.xlsx`
      XLSX.writeFile(workbook, fileName)

      console.log('【导出Excel】Excel文件生成成功:', fileName)
    } catch (error) {
      console.error('【导出Excel】生成Excel文件失败:', error)
      alert('导出失败，请重试')
    }
  }

  // 改进的斐波那契球算法 - 添加随机扰动使分布更自然
  // ========== 【已删除旧的球体渲染函数】 ==========
  // fibonacciSphere, renderSphere, startIdleRotation, startFastRotation, stopRotationSmoothly
  // 已改用 TagCloud3D 组件

const handleDrawResult = (msg) => {
  // WebSocket返回的结果处理
  if (msg.type === 'draw_result' && msg.winners) {
    // 更新剩余数量
    if (currentPrize.value) {
      currentPrize.value.remaining -= msg.winners.length
    }
    
    // 恢复云标签速度
    cloudSpeed.value = 0.5
    
    // 球体容器平滑落回原位
    if (sphereContainerRef.value) {
      gsap.to(sphereContainerRef.value, {
        y: SPHERE_IDLE_Y, // 落回待机高度
        scale: 1, // 恢复初始大小
        duration: 1.5,
        ease: 'power2.out'
      })
    }
    
    // 马匹也落回原位
    if (horseLeftRef.value) {
      gsap.to(horseLeftRef.value, {
        y: 0,
        duration: 1.2,
        ease: 'power2.out'
      })
    }
    if (horseRightRef.value) {
      gsap.to(horseRightRef.value, {
        y: 0,
        duration: 1.2,
        ease: 'power2.out'
      })
    }
    
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

        // 隐藏马匹
        hideHorseAndSphere()

      // 撒花
      confetti({
        particleCount: 200,
        spread: 90,
        origin: {y: 0.5},
        colors: ['#FFD700', '#FFA500', '#FF6347', '#FF1493']
      })
        // 移除自动关闭：等待操作员手动点击屏幕或按空格键才返回
    }, 2000) // 等待2秒减速完成
  }
}

  // ========== 【已删除 stopRotationSmoothly 函数】 ==========
  // 已改用 TagCloud3D 组件的速度控制

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
  // 【性能优化】已删除 startDynamicDepthUpdate 和 stopDynamicDepthUpdate
  // 不再使用 requestAnimationFrame 循环，改用纯 CSS/GSAP 动画
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
  perspective: 800px !important; /* 【核心修复】800px的透视会让"近大远小"的效果非常明显，球体立马就会"鼓"出来 */
  perspective-origin: center center; /* 透视原点居中 */
  display: flex; /* 强制flex布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  transform-style: preserve-3d !important; /* 【强制3D】确保3D变换传递 */
}

/* ========== 【马匹样式】 ========== */
.horse-wrapper {
  position: absolute;
    top: calc(50% + 320px); /* 往下移，让马匹位置更低 */
    width: 240px; /* 稍微缩小马匹 */
  height: auto;
  will-change: transform;
    transform: translateY(-50%);
  pointer-events: none;
    z-index: 20 !important; /* 马匹层 */
}

.horse-left {
    left: calc(50% - 250px); /* 调整马匹位置，适配缩小后的球体 */
}

.horse-right {
    right: calc(50% - 250px); /* 调整马匹位置，适配缩小后的球体 */
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

  /* ========== 【TagCloud3D 容器样式】 ========== */
  .tag-cloud-wrapper {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 600px;
    height: 600px;
    transform: translate(-50%, -50%); /* 居中，不设置 translateY，让 GSAP 控制垂直位置 */
    z-index: 30 !important; /* 【关键修复】球体容器永远在马匹上方 */
    pointer-events: none;
    will-change: transform; /* 优化动画性能 */
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

  /* ========== 【已删除旧的球体相关动画和样式】 ========== */
  /* 已改用 TagCloud3D 组件 */

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

  <!-- 非 scoped 样式：已删除旧的球体卡片样式，改用 TagCloud3D 组件 -->
  <style>
  /* TagCloud3D 组件使用自己的样式，无需额外样式 */
  </style>
