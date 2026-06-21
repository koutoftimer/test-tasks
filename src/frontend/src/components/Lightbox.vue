<template>
  <div class="lightbox-overlay" @click.self="$emit('close')">
    <button class="lightbox-close" @click="$emit('close')">&times;</button>
    <img :src="src" class="lightbox-image" alt="Image" />
  </div>
</template>

<script setup>
defineProps({ src: String })
defineEmits(['close'])
</script>

<style scoped>
.lightbox-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.85); display: flex; align-items: center;
  justify-content: center; z-index: 1000; cursor: pointer;
}
.lightbox-close {
  position: absolute; top: 20px; right: 30px; background: none; border: none;
  color: #fff; font-size: 36px; cursor: pointer; z-index: 1001;
}
.lightbox-image {
  max-width: 90vw; max-height: 90vh; border-radius: 4px; cursor: default;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}
</style>
