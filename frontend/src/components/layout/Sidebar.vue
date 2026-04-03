<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { label: 'ダッシュボード', icon: '📊', to: '/dashboard' },
  { label: 'FAQ管理', icon: '📋', to: '/faqs' },
  { label: 'チャット履歴', icon: '💬', to: '/chat-history' },
]

const isActive = (path) => route.path === path

function handleLogout() {
  authStore.logout()
}
</script>

<template>
  <aside class="fixed left-0 top-0 w-64 h-screen bg-salon-brown flex flex-col z-30">
    <!-- Logo -->
    <div class="px-6 pt-8 pb-6">
      <h1 class="text-2xl font-light tracking-widest text-salon-gold">BLOOM</h1>
      <p class="text-xs text-salon-brown-light mt-1">Hair Salon 管理画面</p>
    </div>

    <!-- Divider -->
    <div class="mx-6 h-px bg-salon-brown-light/20 mb-4"></div>

    <!-- Navigation -->
    <nav class="flex-1 px-3">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-4 py-3 mb-1 rounded-lg text-sm transition-all duration-200"
        :class="
          isActive(item.to)
            ? 'bg-salon-brown-light/30 text-white border-l-4 border-salon-gold pl-3'
            : 'text-salon-brown-light/80 hover:text-white hover:bg-salon-brown-light/15 border-l-4 border-transparent pl-3'
        "
      >
        <span class="text-lg">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Logout -->
    <div class="px-6 pb-6">
      <div class="h-px bg-salon-brown-light/20 mb-4"></div>
      <button
        @click="handleLogout"
        class="flex items-center gap-2 text-sm text-salon-brown-light hover:text-white transition-colors duration-200 w-full"
      >
        <span>🚪</span>
        <span>ログアウト</span>
      </button>
    </div>
  </aside>
</template>
