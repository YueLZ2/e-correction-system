<!-- src/frontend/src/components/ExpertPanel.vue -->
<template>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold text-gray-800">专家建议</h3>
    <div class="grid grid-cols-3 gap-4">
      <button
        v-for="expert in experts"
        :key="expert.id"
        @click="selectExpert(expert.id)"
        :class="[
          'p-4 rounded-lg text-center transition-colors',
          selectedExpert === expert.id
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
        ]"
      >
        {{ expert.name }}
      </button>
    </div>

    <div v-if="currentSuggestions.length > 0" class="mt-6 space-y-4">
      <div
        v-for="(suggestion, index) in currentSuggestions"
        :key="index"
        class="bg-gray-50 rounded-lg p-4"
      >
        <div class="flex items-start space-x-4">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <span class="text-blue-600 font-medium">{{ index + 1 }}</span>
            </div>
          </div>
          <div class="flex-1">
            <p class="text-gray-700">{{ suggestion }}</p>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="text-center text-gray-500 py-8">
      请选择专家查看建议
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'ExpertPanel',
  setup() {
    const store = useStore()
    const selectedExpert = ref(null)

    const experts = [
      { id: 1, name: '业务专家' },
      { id: 2, name: '流程专家' },
      { id: 3, name: '技术专家' }
    ]

    const currentSuggestions = computed(() => {
      if (!selectedExpert.value) return []
      return store.getters['bpmn/getExpertSuggestions'](selectedExpert.value)
    })

    const selectExpert = (expertId) => {
      selectedExpert.value = expertId
      store.dispatch('bpmn/fetchExpertSuggestions', expertId)
    }

    return {
      experts,
      selectedExpert,
      currentSuggestions,
      selectExpert
    }
  }
}
</script>