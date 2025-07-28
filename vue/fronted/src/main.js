// src/frontend/src/main.js
import { createApp } from 'vue'
import { createStore } from 'vuex'
import App from './App.vue'
import bpmnStore from './store/bpmn'
import './assets/main.css'

window.CHECK_CONNECTION = () => {
  // 添加时间戳防止缓存
  const timestamp = new Date().getTime()
  return fetch('/api/health-check?timestamp=' + timestamp)
    .then((res) => res.json())
    .catch((error) => {
      console.error('Health check failed:', error)
      return { status: 'error' }
    })
}

// 在组件中调用（例如 BPMNUploader.vue）
export default {
  mounted() {
    // 页面加载时检测一次
    this.checkConnection()
    
    // 每 30 秒检测一次（可选）
    setInterval(() => {
      this.checkConnection()
    }, 30000)
  },
  methods: {
    async checkConnection() {
      try {
        const response = await window.CHECK_CONNECTION()
        console.log('Connection status:', response.status)
      } catch (error) {
        console.error('检测失败:', error)
      }
    }
  }
}

// Create Vuex store
const store = createStore({
  modules: {
    bpmn: bpmnStore
  }
})

// Create and mount Vue application
const app = createApp(App)
app.use(store)
app.mount('#app')

// Register global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误：', err)
  console.error('错误信息：', info)
}