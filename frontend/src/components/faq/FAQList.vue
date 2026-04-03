<script setup>
defineProps({
  faqs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['edit', 'delete'])

const categoryColors = {
  '営業情報': 'bg-emerald-100 text-emerald-800',
  'メニュー・料金': 'bg-purple-100 text-purple-800',
  '予約関連': 'bg-blue-100 text-blue-800',
  'その他': 'bg-gray-100 text-gray-700',
}

function getCategoryClass(category) {
  return categoryColors[category] || 'bg-gray-100 text-gray-700'
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

function handleDelete(faqId) {
  if (window.confirm('このFAQを削除しますか？')) {
    emit('delete', faqId)
  }
}
</script>

<template>
  <div class="bg-salon-white rounded-xl shadow-sm border border-salon-beige/50 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="bg-salon-cream/50">
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              カテゴリ
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              質問
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              回答
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-salon-brown-light uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-salon-beige/30">
          <tr
            v-for="faq in faqs"
            :key="faq.id"
            class="hover:bg-salon-cream/30 transition-colors"
          >
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="getCategoryClass(faq.category)"
              >
                {{ faq.category }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-salon-brown">
              {{ truncate(faq.question, 60) }}
            </td>
            <td class="px-6 py-4 text-sm text-salon-brown-light">
              {{ truncate(faq.answer, 80) }}
            </td>
            <td class="px-6 py-4 text-right">
              <button
                @click="emit('edit', faq)"
                class="text-salon-gold hover:text-salon-gold-dark transition-colors mr-3 text-sm font-medium"
              >
                編集
              </button>
              <button
                @click="handleDelete(faq.id)"
                class="text-red-400 hover:text-red-600 transition-colors text-sm font-medium"
              >
                削除
              </button>
            </td>
          </tr>
          <tr v-if="!faqs || faqs.length === 0">
            <td colspan="4" class="px-6 py-12 text-center text-sm text-salon-brown-light/60">
              FAQが登録されていません
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
