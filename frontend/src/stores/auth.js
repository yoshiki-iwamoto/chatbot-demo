import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref('')

  const isAuthenticated = computed(() => !!token.value)

  async function login(usernameInput, password) {
    const response = await api.post('/auth/login', {
      username: usernameInput,
      password,
    })
    token.value = response.data.access_token
    username.value = usernameInput
    localStorage.setItem('token', token.value)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    router.push('/login')
  }

  return { token, username, isAuthenticated, login, logout }
})
