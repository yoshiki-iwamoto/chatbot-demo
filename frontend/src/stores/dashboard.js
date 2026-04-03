import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref(null)
  const loading = ref(false)

  async function fetchStats() {
    loading.value = true
    try {
      const response = await api.get('/dashboard/stats')
      stats.value = response.data
    } finally {
      loading.value = false
    }
  }

  return { stats, loading, fetchStats }
})
