<template>
  <div class="comment-item" :class="{ 'has-replies': repliesCount > 0 }">
    <div class="comment-card">
      <div class="comment-header">
        <img v-if="comment.profile?.avatar" :src="mediaUrl(comment.profile.avatar)" class="comment-avatar" />
        <svg v-else class="comment-avatar comment-avatar-placeholder" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <span class="comment-author">{{ comment.profile ? comment.profile.username : 'Anonymous' }}</span>
        <a v-if="comment.profile?.homepage" :href="comment.profile.homepage" class="comment-homepage" target="_blank" rel="noopener" title="Homepage">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
        </a>
        <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
      </div>
      <div class="comment-text" v-html="sanitizeHtml(comment.text)"></div>
      <div v-if="comment.attachments?.length" class="comment-files">
        <div v-for="att in comment.attachments" :key="att.id" class="comment-file">
          <img v-if="att.file_type === 'image'" :src="mediaUrl(att.file)" alt="Attachment" class="comment-image" @click="store.openLightbox(mediaUrl(att.file))" />
          <a v-else :href="mediaUrl(att.file)" target="_blank" class="file-link" download>Download file</a>
        </div>
      </div>
      <div class="comment-actions">
        <span v-if="voteError" class="vote-error">{{ voteError }}</span>
        <button class="btn-vote" :class="{ active: comment.is_liked }" @click="handleVote('like')">
          <svg class="vote-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
          </svg>
          <span class="vote-count">{{ comment.like_count }}</span>
        </button>
        <button class="btn-vote" :class="{ active: comment.is_disliked }" @click="handleVote('dislike')">
          <svg class="vote-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
          </svg>
          <span class="vote-count">{{ comment.dislike_count }}</span>
        </button>
        <span class="actions-divider"></span>
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
      v-for="reply in comment.replies || []"
      :key="reply.id"
      :comment="reply"
      :depth="depth + 1"
      :show-replies="true"
      @reply-created="(id) => emit('reply-created', id)"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useCommentStore } from '../stores/comment.js'
import CommentForm from './CommentForm.vue'
import { mediaUrl } from '../utils/media.js'

const props = defineProps({
  comment: Object,
  depth: { type: Number, default: 0 },
  showReplies: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'reply-created'])

const store = useCommentStore()
const auth = useAuthStore()
const showReplyForm = ref(false)
const voteError = ref('')

const repliesCount = computed(() => props.comment.reply_count ?? props.comment.replies?.length ?? 0)
const showRepliesLink = computed(() => !props.showReplies && repliesCount.value > 0)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString()
}

function handleReplyCreated(reply) {
  showReplyForm.value = false
  emit('reply-created', props.comment.id)
  store.addReply(props.comment.id, reply)
}

async function handleVote(voteType) {
  if (!auth.isAuthenticated) {
    voteError.value = 'Please log in to vote'
    setTimeout(() => { voteError.value = '' }, 3000)
    return
  }
  voteError.value = ''
  try {
    const isActive = voteType === 'like' ? props.comment.is_liked : props.comment.is_disliked
    if (isActive) {
      const data = await store.removeVote(props.comment.id)
      props.comment.is_liked = false
      props.comment.is_disliked = false
      props.comment.like_count = data.like_count
      props.comment.dislike_count = data.dislike_count
    } else {
      const data = await store.voteComment(props.comment.id, voteType)
      props.comment.is_liked = voteType === 'like'
      props.comment.is_disliked = voteType === 'dislike'
      props.comment.like_count = data.like_count
      props.comment.dislike_count = data.dislike_count
    }
  } catch {
    voteError.value = 'Failed to vote. Try logging in again.'
    setTimeout(() => { voteError.value = '' }, 3000)
  }
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
.comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.comment-author { font-weight: 600; color: #1a73e8; font-size: 14px; }
.comment-avatar { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.comment-avatar-placeholder { color: #bbb; }
.comment-date { color: #999; font-size: 12px; margin-left: auto; }
.comment-homepage { color: #888; display: inline-flex; align-items: center; text-decoration: none; }
.comment-homepage:hover { color: #1a73e8; }
.comment-text { font-size: 14px; line-height: 1.6; color: #333; margin-bottom: 8px; word-break: break-word; }
.comment-text :deep(a) { color: #1a73e8; }
.comment-text :deep(code) { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
.comment-text :deep(i) { font-style: italic; }
.comment-text :deep(strong) { font-weight: 700; }
.comment-files { display: flex; flex-wrap: wrap; gap: 8px; }
.comment-file { }
.comment-image { max-width: 320px; max-height: 240px; border-radius: 4px; cursor: pointer; border: 1px solid #e0e0e0; }
.file-link { color: #1a73e8; font-size: 13px; }
.comment-actions { display: flex; align-items: center; gap: 12px; padding-top: 6px; border-top: 1px solid #f0f0f0; }
.btn-vote { background: none; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 3px; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #888; transition: color 0.15s; }
.btn-vote:hover { color: #1a73e8; background: #e8f0fe; }
.btn-vote.active { color: #1a73e8; }
.btn-vote.active .vote-icon { stroke: #1a73e8; }
.vote-error { color: #d93025; font-size: 12px; flex: 1 1 100%; margin-bottom: 4px; }
.vote-icon { width: 14px; height: 14px; }
.vote-count { font-size: 12px; line-height: 1; }
.actions-divider { width: 1px; height: 14px; background: #e0e0e0; }
.btn-reply { background: none; border: none; color: #1a73e8; font-size: 12px; cursor: pointer; padding: 2px 8px; border-radius: 3px; }
.btn-reply:hover { background: #e8f0fe; }
.btn-show-replies { background: none; border: none; color: #1a73e8; font-size: 12px; cursor: pointer; padding: 2px 8px; border-radius: 3px; font-weight: 500; }
.btn-show-replies:hover { background: #e8f0fe; }
</style>
