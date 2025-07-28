src/frontend/src/App.vue
<template>
  <div class="min-h-screen bg-gray-100">
    <Header />
    <main class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- 左侧面板 -->
        <div class="bg-white rounded-lg shadow-lg p-6">
          <BPMNUploader />
          <ExpertPanel class="mt-6" />
        </div>
        <!-- 右侧面板 -->
        <div class="bg-white rounded-lg shadow-lg p-6">
          <BPMNViewer />
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Header from './components/Header.vue'
import BPMNUploader from './components/BPMNUploader.vue'
import BPMNViewer from './components/BPMNViewer.vue'
import ExpertPanel from './components/ExpertPanel.vue'
import './assets/main.css'

export default {
  name: 'App',
  components: {
    Header,
    BPMNUploader,
    BPMNViewer,
    ExpertPanel
  }
}
</script>