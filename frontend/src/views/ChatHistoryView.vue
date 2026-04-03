<script setup>
import { ref, onMounted } from 'vue'
import { useChatHistoryStore } from '../stores/chatHistory'
import UserList from '../components/chat/UserList.vue'
import ChatThread from '../components/chat/ChatThread.vue'

const chatHistoryStore = useChatHistoryStore()

const dateFrom = ref('')
const dateTo = ref('')

function selectUser(userId) {
  chatHistoryStore.fetchMessages(userId, dateFrom.value || undefined, dateTo.value || undefined)
}

function applyDateFilter() {
  if (chatHistoryStore.selectedUserId) {
    chatHistoryStore.fetchMessages(
      chatHistoryStore.selectedUserId,
      dateFrom.value || undefined,
      dateTo.value || undefined
    )
  }
}

onMounted(() => {
  chatHistoryStore.fetchUsers()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-semibold text-salon-brown">チャット履歴</h1>
      <p class="text-sm text-salon-brown-light mt-1">ユーザーとの会話履歴を確認できます</p>
    </div>

    <!-- Date Filter -->
    <div
      v-if="chatHistoryStore.selectedUserId"
      class="flex items-center gap-4 mb-6"
    >
      <div class="flex items-center gap-2">
        <label class="text-sm text-salon-brown-light">開始日</label>
        <input
          v-model="dateFrom"
          type="date"
          @change="applyDateFilter"
          class="px-3 py-1.5 rounded-lg border border-salon-beige text-sm text-salon-brown bg-salon-white focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors"
        />
      </div>
      <div class="flex items-center gap-2">
        <label class="text-sm text-salon-brown-light">終了日</label>
        <input
          v-model="dateTo"
          type="date"
          @change="applyDateFilter"
          class="px-3 py-1.5 rounded-lg border border-salon-beige text-sm text-salon-brown bg-salon-white focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="chatHistoryStore.loading && !chatHistoryStore.selectedUserId" class="flex items-center justify-center py-20">
      <div class="text-salon-brown-light">読み込み中...</div>
    </div>

    <!-- Two-panel layout -->
    <div v-else class="flex gap-6">
      <!-- Left Panel: User List -->
      <div class="w-80 shrink-0">
        <UserList
          :users="chatHistoryStore.users"
          :selected-user-id="chatHistoryStore.selectedUserId"
          @select="selectUser"
        />
      </div>

      <!-- Right Panel: Chat Thread or Empty State -->
      <div class="flex-1 min-w-0">
        <ChatThread
          v-if="chatHistoryStore.selectedUserId"
          :messages="chatHistoryStore.messages"
        />
        <div
          v-else
          class="bg-salon-white rounded-xl shadow-sm border border-salon-beige/50 flex items-center justify-center h-[calc(100vh-16rem)]"
        >
          <div class="text-center">
            <div class="text-4xl mb-3 opacity-30">💬</div>
            <p class="text-salon-brown-light/60 text-sm">ユーザーを選択してください</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
