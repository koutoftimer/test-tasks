<template>
  <div class="app">
    <div class="container">
      <h1>Comments</h1>
      <CommentForm
        @comment-created="handleCommentCreated"
        @refresh-captcha="refreshCaptchaKey"
        :captcha-key="captchaKey"
        :captcha-url="captchaUrl"
      />
      <SortControls
        :sort-by="sortBy"
        @sort="handleSort"
      />
      <CommentList
        :comments="comments"
        :loading="loading"
        :error="error"
        @reply="openReplyForm"
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
import CommentItem from './components/CommentItem.vue'
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

const captchaKey = ref('')
const captchaUrl = ref('')
const lightboxImage = ref(null)
const previewData = ref(null)

provide('openLightbox', (url) => { lightboxImage.value = url })
provide('openPreview', (data) => { previewData.value = data })

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
  fetchComments()
  refreshCaptchaKey()
}

function handleSort(field) {
  setSort(field)
}

function handleGoToPage(p) {
  goToPage(p)
}

function openReplyForm(parentId) {
  const el = document.getElementById('reply-to-' + parentId)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
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

a {
  color: #1a73e8;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
