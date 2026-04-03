<script setup>
defineProps({
  title: { type: String, required: true },
  value: { type: [Number, String], required: true },
  icon: { type: String, required: true },
})
</script>

<template>
  <div class="bg-salon-white rounded-xl shadow-sm border border-salon-beige/50 p-6 relative overflow-hidden">
    <!-- Decorative accent -->
    <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-salon-gold to-salon-accent"></div>

    <!-- Icon -->
    <div class="absolute top-5 right-5 text-2xl opacity-80">
      {{ icon }}
    </div>

    <!-- Value -->
    <div class="text-3xl font-bold text-salon-brown mt-2">
      {{ value }}
    </div>

    <!-- Title -->
    <div class="text-sm text-salon-brown-light mt-1">
      {{ title }}
    </div>
  </div>
</template>
