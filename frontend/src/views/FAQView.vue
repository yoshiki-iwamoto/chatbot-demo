<script setup>
import { ref, onMounted, computed } from 'vue'
import { useFaqStore } from '../stores/faq'
import FAQList from '../components/faq/FAQList.vue'
import FAQForm from '../components/faq/FAQForm.vue'

const faqStore = useFaqStore()

const showForm = ref(false)
const editingFaq = ref(null)

const categories = [
  { label: 'すべて', value: null },
  { label: '営業情報', value: '営業情報' },
  { label: 'メニュー・料金', value: 'メニュー・料金' },
  { label: '予約関連', value: '予約関連' },
  { label: 'その他', value: 'その他' },
]

const activeCategory = ref(null)

const filteredFaqs = computed(() => {
  if (!activeCategory.value) return faqStore.faqs
  return faqStore.faqs.filter((f) => f.category === activeCategory.value)
})

function selectCategory(value) {
  activeCategory.value = value
  faqStore.selectedCategory = value
  faqStore.fetchFaqs(value)
}

function openCreateForm() {
  editingFaq.value = null
  showForm.value = true
}

function openEditForm(faq) {
  editingFaq.value = { ...faq }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingFaq.value = null
}

async function handleDelete(faqId) {
  await faqStore.deleteFaq(faqId)
}

function handleSaved() {
  faqStore.fetchFaqs(activeCategory.value)
}

onMounted(() => {
  faqStore.fetchFaqs()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-salon-brown">FAQ管理</h1>
        <p class="text-sm text-salon-brown-light mt-1">よくある質問の追加・編集ができます</p>
      </div>
      <button
        @click="openCreateForm"
        class="flex items-center gap-2 bg-salon-gold hover:bg-salon-gold-dark text-white px-5 py-2.5 rounded-lg transition-colors text-sm font-medium shadow-sm"
      >
        <span class="text-lg leading-none">+</span>
        <span>新規追加</span>
      </button>
    </div>

    <!-- Category Tabs -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="cat in categories"
        :key="cat.label"
        @click="selectCategory(cat.value)"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        :class="
          activeCategory === cat.value
            ? 'bg-salon-gold text-white shadow-sm'
            : 'bg-salon-white text-salon-brown-light hover:bg-salon-beige/50 border border-salon-beige/50'
        "
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="faqStore.loading" class="flex items-center justify-center py-20">
      <div class="text-salon-brown-light">読み込み中...</div>
    </div>

    <!-- FAQ List -->
    <FAQList
      v-else
      :faqs="filteredFaqs"
      @edit="openEditForm"
      @delete="handleDelete"
    />

    <!-- FAQ Form Modal -->
    <FAQForm
      v-if="showForm"
      :faq="editingFaq"
      @close="closeForm"
      @saved="handleSaved"
    />
  </div>
</template>
