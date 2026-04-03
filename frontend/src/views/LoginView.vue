<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

async function handleSubmit() {
  error.value = ''
  isLoading.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'ログインに失敗しました。'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-salon-cream flex items-center justify-center px-4">
    <div class="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-light tracking-widest text-salon-brown">BLOOM</h1>
        <p class="text-sm text-salon-brown-light mt-1">Hair Salon</p>
        <div class="h-px bg-salon-gold w-16 mx-auto mt-4"></div>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-500 text-sm text-center"
      >
        {{ error }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-salon-brown-light mb-1.5">
            ユーザー名
          </label>
          <input
            v-model="username"
            type="text"
            required
            autocomplete="username"
            class="w-full px-4 py-3 rounded-lg border border-salon-beige bg-salon-cream/50 text-salon-brown placeholder-salon-brown-light/50 focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors"
            placeholder="ユーザー名を入力"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-salon-brown-light mb-1.5">
            パスワード
          </label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full px-4 py-3 rounded-lg border border-salon-beige bg-salon-cream/50 text-salon-brown placeholder-salon-brown-light/50 focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors"
            placeholder="パスワードを入力"
          />
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-salon-gold hover:bg-salon-gold-dark text-white font-medium py-3 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isLoading">ログイン中...</span>
          <span v-else>ログイン</span>
        </button>
      </form>

      <!-- Footer -->
      <p class="text-center text-xs text-salon-brown-light/50 mt-8">
        BLOOM Admin Panel
      </p>
    </div>
  </div>
</template>
