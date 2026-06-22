<template>
  <div class="app">
    <div class="container">
      <h1>Comments</h1>
      <button v-if="!showForm" class="btn-leave-comment" @click="showForm = true">
        Leave a comment
      </button>
      <CommentForm
        v-if="showForm"
        @comment-created="handleCommentCreated"
        @cancel="showForm = false"
      />
      <SortControls
        :sort-by="sortBy"
        @sort="handleSort"
      />
      <CommentList
        :comments="comments"
        :loading="loading"
        :error="error"
      />
      <Pagination
        :page="page"
        :total-pages="totalPages"
        @go-to-page="handleGoToPage"
      />
    </div>
    <Lightbox
      v-if="lightboxImage"
      :src="lightboxImage"
      @close="lightboxImage = null"
    />
    <PreviewModal
      v-if="previewData"
      :data="previewData"
      @close="previewData = null"
    />
  </div>
</template>

<script setup>
import { onMounted, ref, provide } from 'vue'
import CommentForm from './components/CommentForm.vue'
import CommentList from './components/CommentList.vue'
import SortControls from './components/SortControls.vue'
import Pagination from './components/Pagination.vue'
import Lightbox from './components/Lightbox.vue'
import PreviewModal from './components/PreviewModal.vue'
import { useComments } from './composables/useComments.js'

const {
  comments,
  page,
  totalPages,
  sortBy,
  loading,
  error,
  fetchComments,
  fetchCaptcha,
  setSort,
  goToPage,
} = useComments()

const showForm = ref(false)
const captchaKey = ref('')
const captchaUrl = ref('')
const lightboxImage = ref(null)
const previewData = ref(null)

provide('openLightbox', (url) => { lightboxImage.value = url })
provide('openPreview', (data) => { previewData.value = data })
provide('captchaKey', captchaKey)
provide('captchaUrl', captchaUrl)
provide('refreshCaptchaKey', refreshCaptchaKey)

function refreshCaptchaKey() {
  fetchCaptcha().then((data) => {
    captchaKey.value = data.key
    captchaUrl.value = data.image_url
  })
}

onMounted(() => {
  fetchComments()
  refreshCaptchaKey()
})

function handleCommentCreated() {
  showForm.value = false
  fetchComments()
  refreshCaptchaKey()
}

function handleSort(field) {
  setSort(field)
}

function handleGoToPage(p) {
  goToPage(p)
}
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

h1 {
  font-size: 24px;
  margin-bottom: 24px;
  color: #1a1a2e;
}

button {
  cursor: pointer;
  font-family: inherit;
}

.btn-leave-comment {
  display: block;
  margin-bottom: 16px;
  background: #1a73e8;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}
.btn-leave-comment:hover {
  background: #1557b0;
}

a {
  color: #1a73e8;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
