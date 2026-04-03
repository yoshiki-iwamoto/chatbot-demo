<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import StatsCard from '../components/dashboard/StatsCard.vue'
import RecentChats from '../components/dashboard/RecentChats.vue'

const dashboardStore = useDashboardStore()

onMounted(() => {
  dashboardStore.fetchStats()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-semibold text-salon-brown">ダッシュボード</h1>
      <p class="text-sm text-salon-brown-light mt-1">サロンの運営状況を確認できます</p>
    </div>

    <!-- Loading -->
    <div v-if="dashboardStore.loading" class="flex items-center justify-center py-20">
      <div class="text-salon-brown-light">読み込み中...</div>
    </div>

    <template v-else-if="dashboardStore.stats">
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatsCard
          title="今日のメッセージ"
          :value="dashboardStore.stats.today_messages ?? 0"
          icon="💬"
        />
        <StatsCard
          title="週間ユニークユーザー"
          :value="dashboardStore.stats.weekly_unique_users ?? 0"
          icon="👥"
        />
        <StatsCard
          title="FAQ総数"
          :value="dashboardStore.stats.total_faqs ?? 0"
          icon="📋"
        />
      </div>

      <!-- Recent Chats -->
      <RecentChats :chats="dashboardStore.stats.recent_chats || []" />
    </template>
  </div>
</template>
