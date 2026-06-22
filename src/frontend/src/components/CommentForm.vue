<template>
  <div class="comment-form" :class="{ 'reply-form': parentId }">
    <h2>{{ parentId ? 'Reply to comment' : 'Leave a comment' }}</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>Text *</label>
        <HtmlToolbar @insert="insertTag" />
        <textarea ref="textareaRef" v-model="form.text" rows="5" placeholder="Write your comment..." @input="validateText"></textarea>
        <span v-if="errors.text" class="error">{{ errors.text }}</span>
      </div>
      <div class="form-group">
        <label for="file">Attachment</label>
        <input id="file" type="file" accept=".jpg,.jpeg,.png,.gif,.txt" @change="handleFileChange" />
        <span v-if="fileError" class="error">{{ fileError }}</span>
      </div>
      <div class="form-group">
        <label>CAPTCHA</label>
        <div class="captcha-row">
          <img v-if="captchaImage" :src="captchaImage" alt="CAPTCHA" class="captcha-image" />
          <input v-model="captchaValue" type="text" placeholder="Enter CAPTCHA text" class="captcha-input" />
        </div>
        <span v-if="errors.captcha" class="error">{{ errors.captcha }}</span>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-preview" @click="handlePreview">Preview</button>
        <button type="submit" class="btn-submit" :disabled="submitting">{{ submitting ? 'Sending...' : 'Submit' }}</button>
        <button type="button" class="btn-cancel" @click="$emit('cancel')">Cancel</button>
      </div>
      <div v-if="submitError" class="submit-error">{{ submitError }}</div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useCommentStore } from '../stores/comment.js'
import { resizeImage } from '../composables/resizeImage.js'
import HtmlToolbar from './HtmlToolbar.vue'

const emit = defineEmits(['comment-created', 'cancel'])
const props = defineProps({ parentId: { type: Number, default: null } })
const store = useCommentStore()

const textareaRef = ref(null)
const form = reactive({ text: '', file: null })
const errors = reactive({ text: '', captcha: '' })
const fileError = ref('')
const submitError = ref('')
const submitting = ref(false)

const captchaKey = ref('')
const captchaImage = ref('')
const captchaValue = ref('')

onMounted(async () => {
  try {
    const data = await store.fetchCaptcha()
    captchaKey.value = data.key
    captchaImage.value = data.image_url
  } catch {
    submitError.value = 'Failed to load CAPTCHA'
  }
})

function validateText() {
  if (!form.text.trim()) errors.text = 'Text is required'
  else errors.text = ''
}

async function handleFileChange(e) {
  const file = e.target.files[0]
  if (!file) { form.file = null; fileError.value = ''; return }
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'gif', 'txt'].includes(ext)) {
    fileError.value = 'Only JPG, GIF, PNG, and TXT files are allowed'
    e.target.value = ''; form.file = null; return
  }
  if (ext === 'txt' && file.size > 100 * 1024) {
    fileError.value = 'Text file must be under 100KB'
    e.target.value = ''; form.file = null; return
  }
  try {
    form.file = ext === 'txt' ? file : await resizeImage(file)
    fileError.value = ''
  } catch {
    fileError.value = 'Failed to process image'
    form.file = null
  }
}

function insertTag(tag) {
  const textarea = textareaRef.value
  if (!textarea) return
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selected = form.text.substring(start, end)
  let tagOpen, tagClose
  switch (tag) {
    case 'i': tagOpen = '<i>'; tagClose = '</i>'; break
    case 'strong': tagOpen = '<strong>'; tagClose = '</strong>'; break
    case 'code': tagOpen = '<code>'; tagClose = '</code>'; break
    case 'a':
      const href = prompt('Enter URL:')
      if (!href) return
      tagOpen = `<a href="${href}">`; tagClose = '</a>'
      break
    default: return
  }
  form.text = form.text.substring(0, start) + tagOpen + selected + tagClose + form.text.substring(end)
}

async function handlePreview() {
  let previewFile = form.file
  if (previewFile && previewFile.type.startsWith('image/')) {
    previewFile = await resizeImage(previewFile)
  }
  store.openPreview({
    username: 'Preview',
    text: form.text,
    file: previewFile ? URL.createObjectURL(previewFile) : null,
    fileType: previewFile ? previewFile.name.split('.').pop().toLowerCase() : null,
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
      text: form.text,
      parent_id: props.parentId,
      file: form.file,
      captcha_key: captchaKey.value,
      captcha_value: captchaValue.value,
    })
    form.text = ''; form.file = null
    const fileInput = document.querySelector('input[type="file"]')
    if (fileInput) fileInput.value = ''
    emit('comment-created', response)
  } catch (err) {
    submitError.value = err.message
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.comment-form { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #e0e0e0; }
h2 { font-size: 18px; margin-bottom: 16px; color: #1a1a2e; }
.form-group { margin-bottom: 14px; }
label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #555; }
input[type="text"], input[type="email"], input[type="url"], textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #d0d0d0; border-radius: 4px; font-size: 14px; font-family: inherit; transition: border-color 0.2s;
}
input:focus, textarea:focus { outline: none; border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.15); }
textarea { resize: vertical; }
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
.captcha-row { display: flex; align-items: center; gap: 12px; }
.captcha-image { border: 1px solid #d0d0d0; border-radius: 4px; }
.captcha-input { width: 140px; padding: 8px 12px; border: 1px solid #d0d0d0; border-radius: 4px; font-size: 14px; }
</style>