<template>
  <div class="comment-list">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else-if="comments.length === 0" class="empty">No comments yet. Be the first!</div>
    <div v-else class="comments-table">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :depth="0"
      />
    </div>
  </div>
</template>

<script setup>
import CommentItem from './CommentItem.vue'

defineProps({ comments: Array, loading: Boolean, error: String })
</script>

<style scoped>
.loading { text-align: center; padding: 40px; color: #999; }
.error-message { text-align: center; padding: 40px; color: #d93025; }
.empty { text-align: center; padding: 40px; color: #999; font-style: italic; }
.comments-table { width: 100%; }
</style>
