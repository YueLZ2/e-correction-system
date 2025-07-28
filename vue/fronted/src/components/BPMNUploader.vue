<template>
  <div class="space-y-6">
    <!-- BPMN 文件上传区域 -->
    <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
      <div class="space-y-2">
        <div v-if="!bpmnFile" class="flex flex-col items-center">
          <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <label 
            class="cursor-pointer text-blue-600 hover:text-blue-800 relative"
            for="bpmn-upload-input"  
          >
            点击上传
            <input 
              id="bpmn-upload-input" 
              type="file" 
              class="hidden absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".bpmn"
              @change="handleBPMNUpload"
            />
          </label>
          <p class="text-gray-600">点击或拖拽上传 BPMN 文件 (.bpmn)</p>
          <input type="file" class="hidden" accept=".bpmn" @change="handleBPMNUpload" />
        </div>
        <div v-else class="text-left">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">{{ bpmnFile.name }}</span>
            <button @click="removeFile('bpmn')" class="text-red-600">×</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 流程描述文本框 -->
    <textarea
      v-model="description"
      placeholder="请输入流程描述..."
      rows="4"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    ></textarea>
    <input 
    type="file" 
    class="hidden" 
    accept=".txt,.md" 
    @change="handleDescUpload" 
  />
    <!-- 提交按钮 -->
    <button
      @click="submitBPMN"
      :disabled="!bpmnFile || !description"
      class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      提交分析
    </button>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'

export default {
  setup() {
    // 文件状态管理
    const bpmnFile = ref(null)
    const descFile = ref(null)
    const description = ref('')

    // 文件选择处理
    const handleBPMNUpload = (e) => {
      const file = e.target.files?.[0]
      if (file && file.type === 'application/bpmn') {
        bpmnFile.value = file
      } else {
        alert('请上传有效的 BPMN 文件')
        e.target.value = null
      }
    }

    // 表单提交
    const submitBPMN = async () => {
      if (!bpmnFile.value || !description.value) return
      
      // 创建 FormData
      const formData = new FormData()
      formData.append('bpmn_file', bpmnFile.value)
      formData.append('desc_file', descFile.value)
      formData.append('description', description.value)

      try {
        const response = await axios.post('http://localhost:8000/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        // 上传成功提示
        alert('文件上传成功！')
        console.log('后端响应:', response.data)

        // 重置表单
        bpmnFile.value = null
        descFile.value = null
        description.value = ''
      } catch (error) {
        console.error('上传失败:', error)
        alert('上传过程中出现错误')
      }
    }

    // 文件移除
    const removeFile = (type) => {
      if (type === 'bpmn') bpmnFile.value = null
      if (type === 'desc') descFile.value = null
    }

    return {
      bpmnFile,
      descFile,
      description,
      handleBPMNUpload,
      submitBPMN,
      removeFile
    }
  }
}
</script>

<style scoped>
/* 可选：自定义样式 */
input[type="file"] {
  cursor: pointer;
}
</style>