<script setup>
import { ref, watch } from 'vue'
import { useFaqStore } from '../../stores/faq'

const props = defineProps({
  faq: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'saved'])
const faqStore = useFaqStore()

const isEditing = ref(!!props.faq)
const isLoading = ref(false)
const error = ref('')

const form = ref({
  category: props.faq?.category || '営業情報',
  question: props.faq?.question || '',
  answer: props.faq?.answer || '',
})

const categories = ['営業情報', 'メニュー・料金', '予約関連', 'その他']

watch(
  () => props.faq,
  (newFaq) => {
    isEditing.value = !!newFaq
    if (newFaq) {
      form.value = {
        category: newFaq.category || '営業情報',
        question: newFaq.question || '',
        answer: newFaq.answer || '',
      }
    } else {
      form.value = { category: '営業情報', question: '', answer: '' }
    }
  },
  { immediate: true }
)

async function handleSave() {
  error.value = ''
  isLoading.value = true
  try {
    if (isEditing.value && props.faq?.id) {
      await faqStore.updateFaq(props.faq.id, form.value)
    } else {
      await faqStore.createFaq(form.value)
    }
    emit('saved')
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.detail || '保存に失敗しました。'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <!-- Overlay -->
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    @click.self="emit('close')"
  >
    <!-- Modal -->
    <div class="bg-white rounded-xl p-6 w-full max-w-lg shadow-2xl">
      <!-- Title -->
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-salon-brown">
          {{ isEditing ? 'FAQ編集' : 'FAQ追加' }}
        </h2>
        <button
          @click="emit('close')"
          class="text-salon-brown-light hover:text-salon-brown transition-colors text-xl"
        >
          &times;
        </button>
      </div>

      <!-- Divider -->
      <div class="h-px bg-salon-beige mb-6"></div>

      <!-- Error -->
      <div
        v-if="error"
        class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-500 text-sm"
      >
        {{ error }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSave" class="space-y-5">
        <!-- Category -->
        <div>
          <label class="block text-sm font-medium text-salon-brown-light mb-1.5">
            カテゴリ
          </label>
          <select
            v-model="form.category"
            class="w-full px-4 py-2.5 rounded-lg border border-salon-beige bg-salon-cream/30 text-salon-brown focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors"
          >
            <option v-for="cat in categories" :key="cat" :value="cat">
              {{ cat }}
            </option>
          </select>
        </div>

        <!-- Question -->
        <div>
          <label class="block text-sm font-medium text-salon-brown-light mb-1.5">
            質問
          </label>
          <textarea
            v-model="form.question"
            required
            rows="3"
            class="w-full px-4 py-2.5 rounded-lg border border-salon-beige bg-salon-cream/30 text-salon-brown placeholder-salon-brown-light/50 focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors resize-none"
            placeholder="質問を入力してください"
          ></textarea>
        </div>

        <!-- Answer -->
        <div>
          <label class="block text-sm font-medium text-salon-brown-light mb-1.5">
            回答
          </label>
          <textarea
            v-model="form.answer"
            required
            rows="4"
            class="w-full px-4 py-2.5 rounded-lg border border-salon-beige bg-salon-cream/30 text-salon-brown placeholder-salon-brown-light/50 focus:border-salon-gold focus:ring-2 focus:ring-salon-gold/20 focus:outline-none transition-colors resize-none"
            placeholder="回答を入力してください"
          ></textarea>
        </div>

        <!-- Buttons -->
        <div class="flex justify-end gap-3 pt-2">
          <button
            type="button"
            @click="emit('close')"
            class="px-5 py-2.5 rounded-lg border border-salon-beige text-salon-brown-light hover:bg-salon-cream transition-colors text-sm font-medium"
          >
            キャンセル
          </button>
          <button
            type="submit"
            :disabled="isLoading"
            class="px-5 py-2.5 rounded-lg bg-salon-gold hover:bg-salon-gold-dark text-white transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">保存中...</span>
            <span v-else>保存</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
