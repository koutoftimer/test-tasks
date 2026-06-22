<template>
  <div>
    <button class="btn-back" @click="router.back()">← Back to all comments</button>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <CommentItem v-else-if="comment" :comment="comment" :depth="0" :show-replies="true" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCommentStore } from '../stores/comment.js'
import CommentItem from '../components/CommentItem.vue'

const route = useRoute()
const router = useRouter()
const store = useCommentStore()

const comment = ref(null)
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const id = Number(route.params.id)
    let found = store.comments.find(c => c.id === id)
    if (!found) {
      found = await store.fetchComment(id)
      store.comments.unshift(found)
    }
    comment.value = found
  } catch (err) {
    error.value = err.message || 'Failed to load comment'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.btn-back {
  display: inline-block;
  margin-bottom: 16px;
  background: none;
  border: 1px solid #d0d0d0;
  color: #555;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
}
.btn-back:hover {
  background: #f5f5f5;
}
.loading { text-align: center; padding: 40px; color: #999; }
.error-message { text-align: center; padding: 40px; color: #d93025; }
</style>
