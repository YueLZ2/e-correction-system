<!-- src/frontend/src/components/BPMNViewer.vue -->
<template>
  <div class="relative">
    <div class="absolute top-0 right-0 space-x-2">
      <button
        @click="zoomIn"
        class="p-2 bg-gray-100 rounded-lg hover:bg-gray-200"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      </button>
      <button
        @click="zoomOut"
        class="p-2 bg-gray-100 rounded-lg hover:bg-gray-200"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
        </svg>
      </button>
    </div>
    <div ref="container" class="w-full h-[600px] border border-gray-300 rounded-lg"></div>
  </div>
</template>

<script>
import BpmnJS from 'bpmn-js'
import { ref, onMounted, watch } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'BPMNViewer',
  setup() {
    const store = useStore()
    const container = ref(null)
    let viewer = null

    onMounted(() => {
      viewer = new BpmnJS({
        container: container.value
      })
    })

    watch(() => store.state.bpmn.currentBPMN, async (newBPMN) => {
      if (newBPMN && viewer) {
        try {
          await viewer.importXML(newBPMN)
          viewer.get('canvas').zoom('fit-viewport')
        } catch (err) {
          console.error('BPMN加载失败:', err)
        }
      }
    })

    const zoomIn = () => {
      if (viewer) {
        viewer.get('canvas').zoom(viewer.get('canvas').zoom() + 0.1)
      }
    }

    const zoomOut = () => {
      if (viewer) {
        viewer.get('canvas').zoom(viewer.get('canvas').zoom() - 0.1)
      }
    }

    return {
      container,
      zoomIn,
      zoomOut
    }
  }
}
</script>