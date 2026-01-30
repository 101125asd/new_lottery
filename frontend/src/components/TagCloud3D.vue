<template>
  <div ref="containerRef" class="tag-cloud-container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  entries: {
    type: Array,
    required: true,
    default: () => [] // 格式: [{ label: '名字', url: '#', target: '_top' }, ...]
  },
  config: {
    type: Object,
    default: () => ({})
  },
  speed: {
    type: Number,
    default: 1 // 旋转速度系数
  }
})

const containerRef = ref(null)
let cloudInstance = null

// --- 核心算法 (移植自 SVG3DTagCloud) ---
class SVG3DTagCloud {
  constructor(element, params) {
    this.element = element
    this.settings = {
      entries: [],
      width: 480,
      height: 480,
      radius: '70%',
      radiusMin: 75,
      bgDraw: false, // 是否画背景
      bgColor: '#000',
      opacityOver: 1.00,
      opacityOut: 0.05,
      opacitySpeed: 6,
      fov: 800,
      speed: 0.5, // 基础速度
      fontFamily: 'Arial, sans-serif',
      fontSize: '16',
      fontColor: '#FFD700', // 金色
      fontWeight: 'bold',
      fontStyle: 'normal',
      fontStretch: 'normal',
      fontToUpperCase: false,
      ...params
    }

    this.entryHolder = []
    this.radius = 0
    this.diameter = 0
    this.mouseReact = true
    this.mousePos = { x: 0, y: 0 }
    this.center2D = { x: 0, y: 0 }
    this.center3D = { x: 0, y: 0, z: 0 }
    this.speed = { x: 0, y: 0 }
    this.position = { sx: 0, cx: 0, sy: 0, cy: 0 }
    this.MATHPI180 = Math.PI / 180
    this.svg = null
    this.svgNS = 'http://www.w3.org/2000/svg'
    this.animationFrameId = null

    this.init()
  }

  init() {
    this.svg = document.createElementNS(this.svgNS, 'svg')
    // 移除鼠标交互，改为自动旋转，或者你可以保留
    // this.svg.addEventListener('mousemove', (e) => this.mouseMoveHandler(e))
    this.element.appendChild(this.svg)

    if (this.settings.bgDraw) {
      const bg = document.createElementNS(this.svgNS, 'rect')
      bg.setAttribute('x', 0)
      bg.setAttribute('y', 0)
      bg.setAttribute('fill', this.settings.bgColor)
      this.svg.appendChild(bg)
    }

    this.addEntries()
    this.reInit()
    this.animloop()

    // 绑定 resize
    this.resizeHandler = () => this.reInit()
    window.addEventListener('resize', this.resizeHandler)
  }

  reInit() {
    const windowWidth = this.element.offsetWidth || window.innerWidth
    const windowHeight = this.element.offsetHeight || window.innerHeight

    // 强制使用容器大小
    const svgWidth = windowWidth
    const svgHeight = windowHeight

    this.center2D = { x: svgWidth / 2, y: svgHeight / 2 }

    // 速度控制：这里你可以修改逻辑让它不受鼠标控制，而是恒定旋转
    // 默认给一个初始速度，让它自动转
    this.speed.x = this.settings.speed / this.center2D.x
    this.speed.y = this.settings.speed / this.center2D.y

    if (svgWidth >= svgHeight)
      this.diameter = svgHeight / 100 * parseInt(this.settings.radius)
    else
      this.diameter = svgWidth / 100 * parseInt(this.settings.radius)

    if (this.diameter < 1) this.diameter = 1
    this.radius = this.diameter / 2

    if (this.radius < this.settings.radiusMin) {
      this.radius = this.settings.radiusMin
      this.diameter = this.radius * 2
    }

    this.svg.setAttribute('width', svgWidth)
    this.svg.setAttribute('height', svgHeight)

    this.setEntryPositions(this.radius)
  }

  setEntryPositions(radius) {
    for (let i = 0; i < this.entryHolder.length; i++) {
      this.setEntryPosition(this.entryHolder[i], radius)
    }
  }

  setEntryPosition(entry, radius) {
    const dx = entry.vectorPosition.x - this.center3D.x
    const dy = entry.vectorPosition.y - this.center3D.y
    const dz = entry.vectorPosition.z - this.center3D.z
    const length = Math.sqrt(dx * dx + dy * dy + dz * dz)

    entry.vectorPosition.x /= length
    entry.vectorPosition.y /= length
    entry.vectorPosition.z /= length
    entry.vectorPosition.x *= radius
    entry.vectorPosition.y *= radius
    entry.vectorPosition.z *= radius
  }

  addEntry(index, entryObj, x, y, z) {
    const entry = {}

    // 创建文字
    entry.element = document.createElementNS(this.svgNS, 'text')
    entry.element.setAttribute('x', 0)
    entry.element.setAttribute('y', 0)
    entry.element.setAttribute('fill', this.settings.fontColor)
    entry.element.setAttribute('font-family', this.settings.fontFamily)
    entry.element.setAttribute('font-size', this.settings.fontSize)
    entry.element.setAttribute('font-weight', this.settings.fontWeight)
    entry.element.setAttribute('text-anchor', 'middle')
    // 增加文字阴影滤镜效果（可选，提升高级感）
    entry.element.style.textShadow = '0 0 5px rgba(0,0,0,0.8)'
    entry.element.textContent = entryObj.label

    // 如果想支持点击，可以在这里加 Link，但我们主要做展示
    this.svg.appendChild(entry.element)

    entry.index = index
    entry.vectorPosition = { x, y, z }
    entry.vector2D = { x: 0, y: 0 }
    return entry
  }

  addEntries() {
    for (let i = 1, l = this.settings.entries.length + 1; i < l; i++) {
      const phi = Math.acos(-1 + (2 * i) / l)
      const theta = Math.sqrt(l * Math.PI) * phi
      const x = Math.cos(theta) * Math.sin(phi)
      const y = Math.sin(theta) * Math.sin(phi)
      const z = Math.cos(phi)
      const entry = this.addEntry(i - 1, this.settings.entries[i - 1], x, y, z)
      this.entryHolder.push(entry)
    }
  }

  render() {
    // 这里的逻辑决定了旋转方式
    // 如果想要自动旋转，忽略 mousePos，使用固定值
    // fx 和 fy 决定了旋转的角度增量
    const fx = this.settings.speed // 这是一个固定增量，让它一直转
    const fy = this.settings.speed * 0.5 // Y轴稍微转一点

    const angleX = fx * this.MATHPI180
    const angleY = fy * this.MATHPI180

    this.position.sx = Math.sin(angleX)
    this.position.cx = Math.cos(angleX)
    this.position.sy = Math.sin(angleY)
    this.position.cy = Math.cos(angleY)

    for (let i = 0; i < this.entryHolder.length; i++) {
      const entry = this.entryHolder[i]

      // 3D 旋转矩阵计算
      const rx = entry.vectorPosition.x
      const rz = entry.vectorPosition.y * this.position.sy + entry.vectorPosition.z * this.position.cy

      entry.vectorPosition.x = rx * this.position.cx + rz * this.position.sx
      entry.vectorPosition.y = entry.vectorPosition.y * this.position.cy + entry.vectorPosition.z * -this.position.sy
      entry.vectorPosition.z = rx * -this.position.sx + rz * this.position.cx

      // 投影到 2D
      const scale = this.settings.fov / (this.settings.fov + entry.vectorPosition.z)
      entry.vector2D.x = entry.vectorPosition.x * scale + this.center2D.x
      entry.vector2D.y = entry.vectorPosition.y * scale + this.center2D.y

      // 更新 DOM
      entry.element.setAttribute('x', entry.vector2D.x)
      entry.element.setAttribute('y', entry.vector2D.y)

      // 根据深度计算透明度
      const opacity = (this.radius - entry.vectorPosition.z) / this.diameter
      // 限制最小透明度，防止太暗看不清
      const finalOpacity = opacity < 0.2 ? 0.2 : opacity
      entry.element.setAttribute('opacity', finalOpacity)
      // 根据深度缩放字体
      entry.element.setAttribute('font-size', this.settings.fontSize * scale)
    }

    // 深度排序（让前面的挡住后面的）
    // SVG 的 z-index 是靠 DOM 顺序决定的，这里其实应该重新 appendChild
    // 但为了性能，通常忽略 DOM 重排，只靠透明度和大小来模拟
  }

  animloop() {
    this.animationFrameId = requestAnimationFrame(() => this.animloop())
    this.render()
  }

  setSpeed(newSpeed) {
    this.settings.speed = newSpeed
  }

  destroy() {
    if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId)
    window.removeEventListener('resize', this.resizeHandler)
    if (this.element && this.svg) {
      this.element.removeChild(this.svg)
    }
  }
}

// --- Vue 逻辑 ---

const initCloud = () => {
  if (cloudInstance) cloudInstance.destroy()

  if (!props.entries || props.entries.length === 0) return

  cloudInstance = new SVG3DTagCloud(containerRef.value, {
    entries: props.entries,
    width: '100%',
    height: '100%',
    radius: '80%',
    radiusMin: 75,
    bgDraw: false,
    opacityOver: 1.00,
    opacityOut: 0.05,
    opacitySpeed: 6,
    fov: 800,
    speed: props.speed, // 初始速度
    fontFamily: 'Oswald, Arial, sans-serif',
    fontSize: '18', // 基础字号
    fontColor: '#FACC15', // Tailwind yellow-400
    fontWeight: 'bold', // 粗体
    ...props.config
  })
}

// 监听数据变化重新渲染
watch(() => props.entries, () => {
  initCloud()
}, { deep: true })

// 监听速度变化（抽奖加速）
watch(() => props.speed, (newVal) => {
  if (cloudInstance) {
    cloudInstance.setSpeed(newVal)
  }
})

onMounted(() => {
  initCloud()
})

onBeforeUnmount(() => {
  if (cloudInstance) cloudInstance.destroy()
})
</script>

<style scoped>
.tag-cloud-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  /* 确保在马匹图层之下 */
  position: relative;
}
</style>