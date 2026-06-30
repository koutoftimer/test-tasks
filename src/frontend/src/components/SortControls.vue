<template>
  <div class="sort-controls">
    <span class="sort-label">Sort by:</span>
    <button
      v-for="option in sortOptions"
      :key="option.value"
      :class="['sort-btn', { active: sortBy.startsWith('-') ? sortBy === '-' + option.value : sortBy === option.value }]"
      @click="$emit('sort', option.value)"
    >
      {{ option.label }}
      <span v-if="sortBy === '-' + option.value" class="arrow">▲</span>
      <span v-else-if="sortBy === option.value" class="arrow">▼</span>
    </button>
  </div>
</template>

<script setup>
defineProps({ sortBy: { type: String, default: '-id' } })
defineEmits(['sort'])

const sortOptions = [
  { value: 'id', label: 'Date' },
  { value: 'author_username', label: 'User Name' },
  { value: 'author_email', label: 'E-mail' },
]
</script>

<style scoped>
.sort-controls {
  display: flex; align-items: center; gap: 8px; margin-bottom: 16px; padding: 10px 0;
  border-bottom: 1px solid #e0e0e0;
}
.sort-label { font-size: 13px; color: #666; font-weight: 600; }
.sort-btn {
  background: none; border: 1px solid #d0d0d0; padding: 6px 14px; border-radius: 4px;
  font-size: 13px; color: #555; cursor: pointer; transition: all 0.2s;
}
.sort-btn:hover { background: #f0f0f0; }
.sort-btn.active { background: #e8f0fe; border-color: #1a73e8; color: #1a73e8; font-weight: 500; }
.arrow { font-size: 10px; margin-left: 2px; }
</style>
