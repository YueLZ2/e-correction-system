<!-- src/frontend/src/components/Header.vue -->
<template>
  <header class="bg-white shadow">
    <div class="container mx-auto px-4 py-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <h1 class="text-2xl font-bold text-gray-800">BPMN流程优化系统</h1>
          <span class="text-gray-500 text-sm">v1.0.0</span>
        </div>
        <div class="flex items-center space-x-4">
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg hover:bg-gray-100"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                v-if="isDarkMode"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          </button>
          <button
            @click="showHelp"
            class="text-gray-600 hover:text-gray-800"
          >
            帮助
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Header',
  setup() {
    const isDarkMode = ref(false)

    const toggleTheme = () => {
      isDarkMode.value = !isDarkMode.value
      // 实现主题切换逻辑
    }

    const showHelp = () => {
      // 实现帮助对话框逻辑
      alert('系统使用帮助')
    }

    return {
      isDarkMode,
      toggleTheme,
      showHelp
    }
  }
}
</script>