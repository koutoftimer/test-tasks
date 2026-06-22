<template>
  <div>
    <button class="btn-back" @click="router.back()">← Back to all comments</button>
    <div v-if="store.currentLoading" class="loading">Loading...</div>
    <div v-else-if="store.currentError" class="error-message">{{ store.currentError }}</div>
    <CommentItem v-else-if="store.currentComment" :comment="store.currentComment" :depth="0" :show-replies="true" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCommentStore } from '../stores/comment.js'
import CommentItem from '../components/CommentItem.vue'

const route = useRoute()
const router = useRouter()
const store = useCommentStore()

onMounted(() => {
  store.fetchCommentDetail(Number(route.params.id))
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
