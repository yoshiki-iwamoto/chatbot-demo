<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
})

const scrollContainer = ref(null)

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

async function scrollToBottom() {
  await nextTick()
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})

watch(
  () => props.messages,
  () => {
    scrollToBottom()
  },
  { deep: true }
)
</script>

<template>
  <div class="bg-salon-white rounded-xl shadow-sm border border-salon-beige/50 flex flex-col overflow-hidden h-[calc(100vh-16rem)]">
    <!-- Header -->
    <div class="px-6 py-3 border-b border-salon-beige/30 shrink-0">
      <h3 class="text-sm font-semibold text-salon-brown">チャット内容</h3>
    </div>

    <!-- Messages -->
    <div
      ref="scrollContainer"
      class="flex-1 overflow-y-auto p-6 space-y-4 bg-salon-cream/30"
    >
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="flex"
        :class="msg.message_type === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div class="max-w-[70%]">
          <!-- Label -->
          <div
            class="text-xs mb-1 px-1"
            :class="msg.message_type === 'user' ? 'text-right text-blue-500/70' : 'text-left text-salon-brown-light/60'"
          >
            {{ msg.message_type === 'user' ? 'ユーザー' : 'ボット' }}
          </div>

          <!-- Bubble -->
          <div
            class="px-4 py-2.5 text-sm leading-relaxed"
            :class="
              msg.message_type === 'user'
                ? 'bg-salon-beige text-salon-brown rounded-tl-xl rounded-tr-xl rounded-bl-xl'
                : 'bg-salon-white border border-salon-beige text-salon-brown rounded-tl-xl rounded-tr-xl rounded-br-xl'
            "
          >
            {{ msg.content }}
          </div>

          <!-- Timestamp -->
          <div
            class="text-xs text-gray-400 mt-1 px-1"
            :class="msg.message_type === 'user' ? 'text-right' : 'text-left'"
          >
            {{ formatTimestamp(msg.timestamp) }}
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="!messages || messages.length === 0"
        class="flex items-center justify-center h-full text-sm text-salon-brown-light/50"
      >
        メッセージがありません
      </div>
    </div>
  </div>
</template>
