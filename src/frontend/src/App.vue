<template>
  <div class="app">
    <div class="container">
      <router-view :key="$route.fullPath" />
    </div>
    <Lightbox
      v-if="store.lightboxImage"
      :src="store.lightboxImage"
      @close="store.closeLightbox()"
    />
    <PreviewModal
      v-if="store.previewData"
      :data="store.previewData"
      @close="store.closePreview()"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useCommentStore } from './stores/comment.js'
import Lightbox from './components/Lightbox.vue'
import PreviewModal from './components/PreviewModal.vue'

const store = useCommentStore()

onMounted(() => {
  store.fetchComments()
  store.refreshCaptchaKey()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  color: #333;
  line-height: 1.6;
}

.app {
  min-height: 100vh;
  padding: 20px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

button {
  cursor: pointer;
  font-family: inherit;
}

a {
  color: #1a73e8;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
