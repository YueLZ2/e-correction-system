// src/frontend/src/store/bpmn.js
export default {
  namespaced: true,
  
  state: {
    currentBPMN: null,
    expertSuggestions: {
      1: [], // 业务专家建议
      2: [], // 流程专家建议
      3: []  // 技术专家建议
    },
    isLoading: false,
    error: null
  },

  mutations: {
    SET_CURRENT_BPMN(state, bpmn) {
      state.currentBPMN = bpmn
    },
    SET_EXPERT_SUGGESTIONS(state, { expertId, suggestions }) {
      state.expertSuggestions[expertId] = suggestions
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading
    },
    SET_ERROR(state, error) {
      state.error = error
    }
  },

  actions: {
    async uploadBPMN({ commit }, formData) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const response = await fetch('/api/v1/bpmn/upload', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) throw new Error('上传失败')
        
        const data = await response.json()
        commit('SET_CURRENT_BPMN', data.bpmn)
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async fetchExpertSuggestions({ commit }, expertId) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      
      try {
        const response = await fetch(`/api/v1/bpmn/suggestions/${expertId}`)
        
        if (!response.ok) throw new Error('获取建议失败')
        
        const data = await response.json()
        commit('SET_EXPERT_SUGGESTIONS', {
          expertId,
          suggestions: data.suggestions
        })
      } catch (error) {
        commit('SET_ERROR', error.message)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },

  getters: {
    getExpertSuggestions: (state) => (expertId) => {
      return state.expertSuggestions[expertId] || []
    },
    isLoading: (state) => state.isLoading,
    hasError: (state) => state.error !== null
  }
}