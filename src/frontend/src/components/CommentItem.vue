<template>
  <div class="comment-item" :class="{ 'has-replies': repliesCount > 0 }">
    <div class="comment-card">
      <div class="comment-header">
        <span class="comment-author">{{ comment.profile.username }}</span>
        <span class="comment-email">{{ comment.profile.email }}</span>
        <a v-if="comment.profile.homepage" :href="comment.profile.homepage" class="comment-homepage" target="_blank" rel="noopener">www</a>
        <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
      </div>
      <div class="comment-text" v-html="sanitizeHtml(comment.text)"></div>
      <div v-if="comment.file" class="comment-file">
        <img v-if="comment.file_type === 'image'" :src="comment.file" alt="Attachment" class="comment-image" @click="store.openLightbox(comment.file)" />
        <a v-else :href="comment.file" target="_blank" class="file-link" download>Download file</a>
      </div>
      <div class="comment-actions">
        <button class="btn-reply" @click="showReplyForm = !showReplyForm">
          {{ showReplyForm ? 'Cancel' : 'Reply' }}
        </button>
        <button v-if="showRepliesLink" class="btn-show-replies" @click="$emit('select', comment)">
          Show replies ({{ repliesCount }})
        </button>
      </div>
    </div>
    <CommentForm
      v-if="showReplyForm"
      :parent-id="comment.id"
      @comment-created="handleReplyCreated"
      @cancel="showReplyForm = false"
    />
    <CommentItem
      v-if="showReplies"
      v-for="reply in comment.replies"
      :key="reply.id"
      :comment="reply"
      :depth="depth + 1"
      :show-replies="true"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useCommentStore } from '../stores/comment.js'
import CommentForm from './CommentForm.vue'

const props = defineProps({
  comment: Object,
  depth: { type: Number, default: 0 },
  showReplies: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])

const store = useCommentStore()
const showReplyForm = ref(false)

const repliesCount = computed(() => props.comment.replies?.length || 0)
const showRepliesLink = computed(() => !props.showReplies && repliesCount.value > 0)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString()
}

function handleReplyCreated(reply) {
  store.addReply(props.comment.id, reply)
  showReplyForm.value = false
}

function sanitizeHtml(text) {
  if (!text) return ''
  const allowedTags = {
    a: ['href', 'title'],
    code: [],
    i: [],
    strong: [],
  }
  const tagPattern = /<\/?(\w+)([^>]*)>/g
  return text.replace(tagPattern, (match, tagName, attrsStr) => {
    const tag = tagName.toLowerCase()
    if (!(tag in allowedTags)) return ''
    if (match.startsWith('</')) return match
    const allowedAttrs = allowedTags[tag]
    const attrPattern = /(\w+)=(["']).*?\2/g
    const cleanAttrs = []
    let attrMatch
    while ((attrMatch = attrPattern.exec(attrsStr)) !== null) {
      if (allowedAttrs.includes(attrMatch[1].toLowerCase())) {
        cleanAttrs.push(attrMatch[0])
      }
    }
    const attrs = cleanAttrs.length ? ' ' + cleanAttrs.join(' ') : ''
    return `<${tag}${attrs}>`
  })
}
</script>

<style scoped>
.comment-item { margin-top: 8px; }
.comment-item > .comment-item { margin-left: 16px; }
.comment-item.has-replies { border-left: 1px solid rgba(26, 115, 232, 0.35); border-radius: 6px; }
.comment-card {
  background: #fafafa; border: 1px solid #e8e8e8; border-radius: 6px; padding: 12px 16px;
  transition: box-shadow 0.2s;
}
.comment-card:hover { box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.comment-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.comment-author { font-weight: 600; color: #1a73e8; font-size: 14px; }
.comment-email { color: #888; font-size: 12px; }
.comment-date { color: #999; font-size: 12px; margin-left: auto; }
.comment-homepage { font-size: 12px; color: #1a73e8; text-decoration: none; }
.comment-homepage:hover { text-decoration: underline; }
.comment-text { font-size: 14px; line-height: 1.6; color: #333; margin-bottom: 8px; word-break: break-word; }
.comment-text :deep(a) { color: #1a73e8; }
.comment-text :deep(code) { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
.comment-text :deep(i) { font-style: italic; }
.comment-text :deep(strong) { font-weight: 700; }
.comment-file { margin-bottom: 8px; }
.comment-image { max-width: 320px; max-height: 240px; border-radius: 4px; cursor: pointer; border: 1px solid #e0e0e0; }
.file-link { color: #1a73e8; font-size: 13px; }
.comment-actions { display: flex; align-items: center; gap: 12px; padding-top: 6px; border-top: 1px solid #f0f0f0; }
.btn-reply { background: none; border: none; color: #1a73e8; font-size: 12px; cursor: pointer; padding: 2px 8px; border-radius: 3px; }
.btn-reply:hover { background: #e8f0fe; }
.btn-show-replies { background: none; border: none; color: #1a73e8; font-size: 12px; cursor: pointer; padding: 2px 8px; border-radius: 3px; font-weight: 500; }
.btn-show-replies:hover { background: #e8f0fe; }
</style>
