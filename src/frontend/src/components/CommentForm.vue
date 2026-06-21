<template>
  <div class="comment-form">
    <h2>Leave a comment</h2>
    <form @submit.prevent="handleSubmit">
      <div class="form-row">
        <div class="form-group">
          <label for="username">User Name *</label>
          <input id="username" v-model="form.username" type="text" placeholder="Latin letters and digits only" @blur="validateUsername" />
          <span v-if="errors.username" class="error">{{ errors.username }}</span>
        </div>
        <div class="form-group">
          <label for="email">E-mail *</label>
          <input id="email" v-model="form.email" type="email" placeholder="your@email.com" @blur="validateEmail" />
          <span v-if="errors.email" class="error">{{ errors.email }}</span>
        </div>
      </div>
      <div class="form-group">
        <label for="homepage">Home page</label>
        <input id="homepage" v-model="form.homepage" type="url" placeholder="https://example.com" @blur="validateHomepage" />
        <span v-if="errors.homepage" class="error">{{ errors.homepage }}</span>
      </div>
      <div class="form-group">
        <label>Text *</label>
        <HtmlToolbar @insert="insertTag" />
        <textarea v-model="form.text" rows="5" placeholder="Write your comment..." @input="validateText"></textarea>
        <span v-if="errors.text" class="error">{{ errors.text }}</span>
      </div>
      <div class="form-group">
        <label for="file">Attachment</label>
        <input id="file" type="file" accept=".jpg,.jpeg,.png,.gif,.txt" @change="handleFileChange" />
        <span v-if="fileError" class="error">{{ fileError }}</span>
      </div>
      <div class="captcha-row">
        <div class="form-group">
          <label>CAPTCHA *</label>
          <img :src="captchaUrl" alt="CAPTCHA" class="captcha-image" />
          <button type="button" class="btn-refresh" @click="$emit('refresh-captcha')">Refresh</button>
          <input v-model="form.captcha_value" type="text" placeholder="Enter CAPTCHA" @input="validateCaptcha" />
          <span v-if="errors.captcha_value" class="error">{{ errors.captcha_value }}</span>
        </div>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-preview" @click="handlePreview">Preview</button>
        <button type="submit" class="btn-submit" :disabled="submitting">{{ submitting ? 'Sending...' : 'Submit' }}</button>
      </div>
      <div v-if="submitError" class="submit-error">{{ submitError }}</div>
    </form>
  </div>
</template>

<script setup>
import { inject, reactive, ref } from 'vue'
import { useComments } from '../composables/useComments.js'
import { resizeImage } from '../composables/resizeImage.js'
import HtmlToolbar from './HtmlToolbar.vue'

const emit = defineEmits(['comment-created', 'refresh-captcha'])
const props = defineProps({ captchaKey: String, captchaUrl: String })
const openPreview = inject('openPreview')

const form = reactive({ username: '', email: '', homepage: '', text: '', captcha_value: '', file: null })
const errors = reactive({ username: '', email: '', homepage: '', text: '', captcha_value: '' })
const fileError = ref('')
const submitError = ref('')
const submitting = ref(false)

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const urlRegex = /^(https?:\/\/)?[\w\-]+(\.[\w\-]+)+[/#?]?.*$/
const usernameRegex = /^[a-zA-Z0-9]+$/

function validateUsername() {
  if (!form.username) errors.username = 'Username is required'
  else if (!usernameRegex.test(form.username)) errors.username = 'Only Latin letters and digits allowed'
  else errors.username = ''
}
function validateEmail() {
  if (!form.email) errors.email = 'E-mail is required'
  else if (!emailRegex.test(form.email)) errors.email = 'Invalid e-mail format'
  else errors.email = ''
}
function validateHomepage() {
  if (form.homepage && !urlRegex.test(form.homepage)) errors.homepage = 'Invalid URL format'
  else errors.homepage = ''
}
function validateText() {
  if (!form.text.trim()) errors.text = 'Text is required'
  else errors.text = ''
}
function validateCaptcha() {
  if (!form.captcha_value) errors.captcha_value = 'CAPTCHA is required'
  else if (!/^[a-zA-Z0-9]+$/.test(form.captcha_value)) errors.captcha_value = 'Only Latin letters and digits'
  else errors.captcha_value = ''
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
  const textarea = document.querySelector('textarea')
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
  openPreview({
    username: form.username || 'Anonymous',
    text: form.text,
    file: previewFile ? URL.createObjectURL(previewFile) : null,
    fileType: previewFile ? previewFile.name.split('.').pop().toLowerCase() : null,
  })
}

async function handleSubmit() {
  validateUsername(); validateEmail(); validateHomepage(); validateText(); validateCaptcha()
  if (Object.values(errors).some(Boolean) || fileError.value) return
  submitting.value = true; submitError.value = ''
  try {
    const { createComment } = useComments()
    await createComment({
      username: form.username,
      email: form.email,
      homepage: form.homepage,
      text: form.text,
      captcha_key: props.captchaKey,
      captcha_value: form.captcha_value,
      file: form.file,
    })
    form.username = ''; form.email = ''; form.homepage = ''; form.text = ''
    form.captcha_value = ''; form.file = null
    const fileInput = document.querySelector('input[type="file"]')
    if (fileInput) fileInput.value = ''
    emit('comment-created')
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
.form-row { display: flex; gap: 16px; }
.form-row .form-group { flex: 1; }
.form-group { margin-bottom: 14px; }
label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #555; }
input[type="text"], input[type="email"], input[type="url"], textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #d0d0d0; border-radius: 4px; font-size: 14px; font-family: inherit; transition: border-color 0.2s;
}
input:focus, textarea:focus { outline: none; border-color: #1a73e8; box-shadow: 0 0 0 2px rgba(26,115,232,0.15); }
textarea { resize: vertical; }
.error { display: block; color: #d93025; font-size: 12px; margin-top: 2px; }
.captcha-row { margin-bottom: 14px; }
.captcha-image { display: block; margin-bottom: 8px; border: 1px solid #d0d0d0; border-radius: 4px; }
.btn-refresh { background: none; border: 1px solid #d0d0d0; padding: 4px 12px; font-size: 12px; border-radius: 4px; margin-bottom: 8px; color: #555; }
.btn-refresh:hover { background: #f5f5f5; }
.form-actions { display: flex; gap: 12px; margin-top: 16px; }
.btn-preview { background: #fff; border: 1px solid #1a73e8; color: #1a73e8; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 500; }
.btn-preview:hover { background: #e8f0fe; }
.btn-submit { background: #1a73e8; border: none; color: #fff; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 500; }
.btn-submit:hover { background: #1557b0; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.submit-error { margin-top: 12px; padding: 8px 12px; background: #fce8e6; border-radius: 4px; color: #d93025; font-size: 13px; }
</style>
