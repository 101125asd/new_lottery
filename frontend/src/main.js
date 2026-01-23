import { createApp } from 'vue'
import './style.css' // 引入我们配置好的 Tailwind 样式
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')