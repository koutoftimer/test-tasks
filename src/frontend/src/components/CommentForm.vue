<template>
  <div class="comment-form" :class="{ 'reply-form': parentId }">
    <h2>{{ parentId ? 'Reply to comment' : 'Leave a comment' }}</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>Text *</label>
        <div class="editor-wrapper">
          <QuillEditor ref="quillRef" :toolbar="toolbar" @update:content="validateText" placeholder="Write your comment..." />
          <div class="custom-toolbar">
            <button type="button" class="ql-btn" title="Insert Image" @click="triggerUpload('image')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              Image
            </button>
            <button type="button" class="ql-btn" title="Insert Text File" @click="triggerUpload('text')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              Text
            </button>
          </div>
        </div>
        <span v-if="errors.text" class="error">{{ errors.text }}</span>
      </div>
      <input ref="fileInputRef" type="file" accept=".jpg,.jpeg,.png,.gif,.txt" style="display:none" @change="handleFileSelected" />
      <span v-if="uploadError" class="error">{{ uploadError }}</span>
      <div class="form-group">
        <label>CAPTCHA</label>
        <div class="captcha-row">
          <img v-if="captchaImage" :src="captchaImage" alt="CAPTCHA" class="captcha-image" @click="refreshCaptcha" />
          <input v-model="captchaValue" type="text" placeholder="Enter CAPTCHA text" class="captcha-input" />
        </div>
        <span v-if="errors.captcha" class="error">{{ errors.captcha }}</span>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-preview" @click="handlePreview">Preview</button>
        <button type="submit" class="btn-submit" :disabled="submitting">{{ submitting ? 'Sending...' : 'Submit' }}</button>
        <button type="button" class="btn-cancel" @click="handleCancel">Cancel</button>
      </div>
      <div v-if="submitError" class="submit-error">{{ submitError }}</div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useCommentStore } from '../stores/comment.js'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import { API_BASE } from '../utils/config.js'
import { resizeImage } from '../composables/resizeImage.js'

const emit = defineEmits(['comment-created', 'cancel'])
const props = defineProps({ parentId: { type: Number, default: null } })
const store = useCommentStore()
const auth = useAuthStore()

const quillRef = ref(null)
const fileInputRef = ref(null)

const toolbar = [
  ['bold', 'italic', 'code'],
  ['link'],
  ['clean'],
]

const errors = reactive({ text: '', captcha: '' })
const fileError = ref('')
const uploadError = ref('')
const submitError = ref('')
const submitting = ref(false)
const uploadType = ref('image')

const captchaKey = ref('')
const captchaImage = ref('')
const captchaValue = ref('')
const attachmentIds = ref([])

onMounted(async () => {
  try {
    const data = await store.fetchCaptcha()
    captchaKey.value = data.key
    captchaImage.value = data.image_url
  } catch {
    submitError.value = 'Failed to load CAPTCHA'
  }
})

function getEditorHTML() {
  return quillRef.value?.getHTML() || ''
}

function getEditorText() {
  return quillRef.value?.getQuill()?.getText()?.trim() || ''
}

function validateText() {
  if (!getEditorText()) errors.text = 'Text is required'
  else errors.text = ''
}

function triggerUpload(type) {
  uploadType.value = type
  const input = fileInputRef.value
  if (input) {
    input.accept = type === 'image' ? '.jpg,.jpeg,.png,.gif' : '.txt'
    input.click()
  }
}

async function handleFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const currentType = uploadType.value
  fileError.value = ''
  uploadError.value = ''
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'gif', 'txt'].includes(ext)) {
    fileError.value = 'Only JPG, GIF, PNG, and TXT files are allowed'
    e.target.value = ''
    return
  }
  try {
    let uploadFile = file
    if (currentType === 'image') {
      uploadFile = await resizeImage(file)
    }
    const result = await store.uploadAttachment(uploadFile)
    attachmentIds.value.push(result.id)
    const url = result.file.startsWith('http') ? result.file : API_BASE + result.file
    const quill = quillRef.value?.getQuill()
    if (quill) {
      const range = quill.getSelection(true)
      if (currentType === 'image') {
        quill.insertEmbed(range.index, 'image', url)
      } else {
        quill.insertText(range.index, 'Download', { link: url })
      }
      quill.setSelection(range.index + 1)
    }
  } catch (err) {
    uploadError.value = err.message
  }
  e.target.value = ''
}

async function handlePreview() {
  const html = getEditorHTML()
  const sanitized = await store.sanitizeHtml(html)
  store.openPreview({
    username: auth.user?.username || 'Anonymous',
    text: sanitized,
  })
}

async function refreshCaptcha() {
  try {
    const data = await store.fetchCaptcha()
    captchaKey.value = data.key
    captchaImage.value = data.image_url
    captchaValue.value = ''
  } catch {
    submitError.value = 'Failed to refresh CAPTCHA'
  }
}

async function handleSubmit() {
  validateText()
  if (errors.text || fileError.value) return
  if (!captchaValue.value.trim()) {
    errors.captcha = 'Please enter the CAPTCHA text'
    return
  }
  submitting.value = true; submitError.value = ''
  try {
    const response = await store.createComment({
      text: getEditorHTML(),
      parent_id: props.parentId,
      captcha_key: captchaKey.value,
      captcha_value: captchaValue.value,
      attachment_ids: attachmentIds.value,
    })
    quillRef.value?.getQuill()?.setContents([])
    attachmentIds.value = []
    emit('comment-created', response)
  } catch (err) {
    submitError.value = err.message
    attachmentIds.value = []
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  attachmentIds.value = []
  emit('cancel')
}
</script>

<style scoped>
.comment-form { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #e0e0e0; }
h2 { font-size: 18px; margin-bottom: 16px; color: #1a1a2e; }
.form-group { margin-bottom: 14px; }
label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #555; }
input[type="text"], input[type="email"], input[type="url"] {
  width: 100%; padding: 8px 12px; border: 1px solid #d0d0d0; border-radius: 4px; font-size: 14px; font-family: inherit; transition: border-color 0.2s;
}
input:focus { outline: none; border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.15); }
.error { display: block; color: #d93025; font-size: 12px; margin-top: 2px; }
.form-actions { display: flex; gap: 12px; margin-top: 16px; }
.btn-preview { background: #fff; border: 1px solid #1a73e8; color: #1a73e8; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 500; }
.btn-preview:hover { background: #e8f0fe; }
.btn-submit { background: #1a73e8; border: none; color: #fff; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 500; }
.btn-submit:hover { background: #1557b0; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-cancel { background: #fff; border: 1px solid #d0d0d0; color: #555; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 500; }
.btn-cancel:hover { background: #f5f5f5; }
.submit-error { margin-top: 12px; padding: 8px 12px; background: #fce8e6; border-radius: 4px; color: #d93025; font-size: 13px; }
.reply-form { margin: 12px 0 8px 16px; padding: 16px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e8e8e8; }
.reply-form h2 { font-size: 15px; margin-bottom: 12px; }
:deep(.ql-editor) { min-height: 120px; font-size: 14px; line-height: 1.6; }
:deep(.ql-toolbar) { border-radius: 4px 4px 0 0; border-bottom: none; }
:deep(.ql-container) { border-radius: 0 0 4px 4px; }
.editor-wrapper { border: 1px solid #d0d0d0; border-radius: 4px; }
.editor-wrapper:focus-within { border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.15); }
:deep(.ql-toolbar), :deep(.ql-container) { border: none !important; }
.custom-toolbar { display: flex; gap: 2px; padding: 4px 8px; border-top: 1px solid #e0e0e0; background: #fafafa; }
.ql-btn { display: inline-flex; align-items: center; gap: 3px; background: none; border: 1px solid transparent; padding: 3px 8px; border-radius: 3px; font-size: 12px; cursor: pointer; color: #555; }
.ql-btn:hover { background: #e8f0fe; color: #1a73e8; border-color: #c6daf9; }
.captcha-row { display: flex; align-items: center; gap: 12px; }
.captcha-image { border: 1px solid #d0d0d0; border-radius: 4px; }
.captcha-input { width: 140px; padding: 8px 12px; border: 1px solid #d0d0d0; border-radius: 4px; font-size: 14px; }
</style>