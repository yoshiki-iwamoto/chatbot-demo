<script setup>
defineProps({
  users: {
    type: Array,
    default: () => [],
  },
  selectedUserId: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['select'])

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
    <div class="px-4 py-3 border-b border-salon-beige/30">
      <h3 class="text-sm font-semibold text-salon-brown">ユーザー一覧</h3>
    </div>

    <!-- User List -->
    <div class="max-h-[calc(100vh-16rem)] overflow-y-auto">
      <button
        v-for="user in users"
        :key="user.user_id"
        @click="emit('select', user.user_id)"
        class="w-full text-left px-4 py-3 border-b border-salon-beige/20 transition-all duration-150 hover:bg-salon-cream/50"
        :class="
          selectedUserId === user.user_id
            ? 'bg-salon-beige/40 border-l-4 border-l-salon-gold'
            : 'border-l-4 border-l-transparent'
        "
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <!-- User ID -->
            <div class="text-sm font-medium text-salon-brown font-mono">
              {{ truncate(user.user_id, 8) }}...
            </div>
            <!-- Last message -->
            <div class="text-xs text-salon-brown-light/70 mt-0.5 truncate">
              {{ truncate(user.last_message, 30) }}
            </div>
          </div>

          <div class="flex flex-col items-end gap-1 shrink-0">
            <!-- Message count badge -->
            <span class="inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1.5 rounded-full bg-salon-gold/15 text-salon-gold-dark text-xs font-medium">
              {{ user.message_count }}
            </span>
            <!-- Timestamp -->
            <span class="text-xs text-salon-brown-light/50 whitespace-nowrap">
              {{ formatTimestamp(user.last_timestamp) }}
            </span>
          </div>
        </div>
      </button>

      <!-- Empty state -->
      <div
        v-if="!users || users.length === 0"
        class="px-4 py-8 text-center text-sm text-salon-brown-light/60"
      >
        ユーザーがいません
      </div>
    </div>
  </div>
</template>
