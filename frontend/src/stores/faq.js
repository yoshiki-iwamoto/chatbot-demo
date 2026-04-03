import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useFaqStore = defineStore('faq', () => {
  const faqs = ref([])
  const loading = ref(false)
  const selectedCategory = ref(null)

  async function fetchFaqs(category) {
    loading.value = true
    try {
      const params = category ? { category } : {}
      const response = await api.get('/faqs', { params })
      faqs.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function createFaq(data) {
    const response = await api.post('/faqs', data)
    faqs.value.push(response.data)
    return response.data
  }

  async function updateFaq(id, data) {
    const response = await api.put(`/faqs/${id}`, data)
    const index = faqs.value.findIndex((f) => f.id === id)
    if (index !== -1) {
      faqs.value[index] = response.data
    }
    return response.data
  }

  async function deleteFaq(id) {
    await api.delete(`/faqs/${id}`)
    faqs.value = faqs.value.filter((f) => f.id !== id)
  }

  return { faqs, loading, selectedCategory, fetchFaqs, createFaq, updateFaq, deleteFaq }
})
