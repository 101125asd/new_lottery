/**
 * 动态获取后端 API 和 WebSocket URL
 * 根据环境自动适配开发和生产环境
 */

/**
 * 获取后端 API 基础 URL
 */
export function getBackendUrl() {
  if (import.meta.env.DEV) {
    // 开发环境：使用 localhost:8000
    return 'http://localhost:8000'
  } else {
    // 生产环境：使用当前页面的协议和主机
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    return `${protocol}//${window.location.hostname}`
  }
}

/**
 * 获取 WebSocket URL
 * @param {string} path - WebSocket 路径，如 '/ws/screen' 或 '/ws/mobile'
 */
export function getWebSocketUrl(path) {
  if (import.meta.env.DEV) {
    // 开发环境：使用 ws://localhost:8000
    return `ws://localhost:8000${path}`
  } else {
    // 生产环境：根据当前页面协议使用 ws 或 wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.hostname}${path}`
  }
}

/**
 * 获取前端 URL（用于生成二维码）
 */
export function getFrontendUrl() {
  if (import.meta.env.DEV) {
    // 开发环境：需要从后端获取 IP
    return null // 需要从后端 API 获取
  } else {
    // 生产环境：使用当前页面的 URL
    const protocol = window.location.protocol
    return `${protocol}//${window.location.hostname}/mobile`
  }
}








