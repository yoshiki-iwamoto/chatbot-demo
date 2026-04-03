import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useChatHistoryStore = defineStore('chatHistory', () => {
  const users = ref([])
  const messages = ref([])
  const selectedUserId = ref(null)
  const loading = ref(false)

  async function fetchUsers() {
    loading.value = true
    try {
      const response = await api.get('/chat-history/users')
      users.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchMessages(userId, dateFrom, dateTo) {
    loading.value = true
    try {
      const params = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const response = await api.get(`/chat-history/users/${userId}/messages`, { params })
      messages.value = response.data
      selectedUserId.value = userId
    } finally {
      loading.value = false
    }
  }

  return { users, messages, selectedUserId, loading, fetchUsers, fetchMessages }
})
