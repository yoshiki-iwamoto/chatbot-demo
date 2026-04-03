<script setup>
import Sidebar from '../components/layout/Sidebar.vue'
</script>

<template>
  <div class="flex min-h-screen">
    <Sidebar />
    <main class="ml-64 flex-1 bg-salon-cream min-h-screen overflow-y-auto p-8">
      <RouterView />
    </main>
  </div>
</template>
