<template>
  <div class="pagination" v-if="totalPages > 1">
    <button :disabled="page <= 1" @click="$emit('go-to-page', page - 1)">Previous</button>
    <button
      v-for="p in pages"
      :key="p"
      :class="['page-btn', { active: p === page }]"
      @click="$emit('go-to-page', p)"
    >{{ p }}</button>
    <button :disabled="page >= totalPages" @click="$emit('go-to-page', page + 1)">Next</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ page: Number, totalPages: Number })
defineEmits(['go-to-page'])

const pages = computed(() => {
  const range = []
  const start = Math.max(1, props.page - 2)
  const end = Math.min(props.totalPages, props.page + 2)
  for (let i = start; i <= end; i++) range.push(i)
  return range
})
</script>

<style scoped>
.pagination { display: flex; justify-content: center; align-items: center; gap: 6px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e0e0e0; }
.pagination button { padding: 6px 14px; border: 1px solid #d0d0d0; background: #fff; border-radius: 4px; font-size: 13px; cursor: pointer; color: #555; }
.pagination button:hover:not(:disabled) { background: #f0f0f0; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.pagination .active { background: #1a73e8; color: #fff; border-color: #1a73e8; }
.page-btn { min-width: 36px; text-align: center; }
</style>
