<script setup>
defineProps({
  chats: {
    type: Array,
    default: () => [],
  },
})

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

function formatTimestamp(ts) {
  if (!ts) return ''
  const date = new Date(ts)
  return date.toLocaleString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="bg-salon-white rounded-xl shadow-sm border border-salon-beige/50 overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-salon-beige/30">
      <h3 class="text-lg font-semibold text-salon-brown">最近のチャット</h3>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="bg-salon-cream/50">
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              ユーザー
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              タイプ
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              内容
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              日時
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-salon-beige/30">
          <tr
            v-for="(chat, index) in chats"
            :key="index"
            class="hover:bg-salon-cream/30 transition-colors"
          >
            <td class="px-6 py-3 text-sm text-salon-brown font-mono">
              {{ truncate(chat.user_id, 8) }}
            </td>
            <td class="px-6 py-3">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="
                  chat.message_type === 'user'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-salon-beige text-salon-brown'
                "
              >
                {{ chat.message_type === 'user' ? 'ユーザー' : 'ボット' }}
              </span>
            </td>
            <td class="px-6 py-3 text-sm text-salon-brown-light">
              {{ truncate(chat.content, 50) }}
            </td>
            <td class="px-6 py-3 text-sm text-salon-brown-light whitespace-nowrap">
              {{ formatTimestamp(chat.timestamp) }}
            </td>
          </tr>
          <tr v-if="!chats || chats.length === 0">
            <td colspan="4" class="px-6 py-8 text-center text-sm text-salon-brown-light/60">
              チャット履歴がありません
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
