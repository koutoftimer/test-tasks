<template>
  <div class="app">
    <div class="container">
      <div class="auth-bar">
        <span v-if="auth.user" class="auth-user">{{ auth.user.username }}</span>
        <button v-if="auth.user" class="btn-logout" @click="handleLogout">Logout</button>
        <template v-else>
          <form class="auth-form" @submit.prevent="handleAuth">
            <input v-model="authUsername" placeholder="Username" required />
            <input v-if="isRegister" v-model="authEmail" type="email" placeholder="Email" required />
            <input v-model="authPassword" type="password" placeholder="Password" required />
            <button type="submit" class="btn-auth">{{ isRegister ? 'Register' : 'Login' }}</button>
          </form>
          <button class="btn-toggle-auth" @click="isRegister = !isRegister">
            {{ isRegister ? 'Have an account? Login' : 'No account? Register' }}
          </button>
        </template>
        <div v-if="authError" class="auth-error">{{ authError }}</div>
      </div>
      <router-view :key="$route.fullPath" />
    </div>
    <Lightbox
      v-if="store.lightboxImage"
      :src="store.lightboxImage"
      @close="store.closeLightbox()"
    />
    <PreviewModal
      v-if="store.previewData"
      :data="store.previewData"
      @close="store.closePreview()"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useAuthStore } from './stores/auth.js'
import { useCommentStore } from './stores/comment.js'
import Lightbox from './components/Lightbox.vue'
import PreviewModal from './components/PreviewModal.vue'

const store = useCommentStore()
const auth = useAuthStore()

const authUsername = ref('')
const authEmail = ref('')
const authPassword = ref('')
const isRegister = ref(false)
const authError = ref('')

onMounted(() => {
  store.fetchComments()
  if (auth.accessToken) {
    auth.fetchUser()
  }
})

async function handleAuth() {
  authError.value = ''
  try {
    if (isRegister.value) {
      await auth.register(authUsername.value, authEmail.value, authPassword.value)
      await auth.login(authUsername.value, authPassword.value)
    } else {
      await auth.login(authUsername.value, authPassword.value)
    }
    authUsername.value = ''
    authEmail.value = ''
    authPassword.value = ''
    isRegister.value = false
    store.fetchComments()
    store.refreshCurrentDetail()
  } catch (err) {
    authError.value = err.response?.data?.detail
      || err.response?.data?.map?.(e => e).join(', ')
      || 'Authentication failed'
  }
}

function handleLogout() {
  auth.logout()
  store.fetchComments()
  store.refreshCurrentDetail()
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

.auth-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  flex-wrap: wrap;
}
.auth-user { font-size: 14px; color: #555; font-weight: 500; }
.auth-form { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.auth-form input {
  padding: 6px 10px; border: 1px solid #d0d0d0; border-radius: 3px;
  font-size: 13px; outline: none; font-family: inherit;
}
.auth-form input:focus { border-color: #1a73e8; }
.btn-auth {
  background: #1a73e8; color: #fff; border: none; padding: 6px 14px;
  border-radius: 3px; font-size: 13px; font-weight: 500;
}
.btn-auth:hover { background: #1557b0; }
.btn-logout {
  background: none; border: 1px solid #d0d0d0; color: #555;
  padding: 6px 14px; border-radius: 3px; font-size: 13px;
}
.btn-logout:hover { background: #f5f5f5; }
.btn-toggle-auth {
  background: none; border: none; color: #1a73e8; font-size: 12px; padding: 0;
}
.btn-toggle-auth:hover { text-decoration: underline; }
.auth-error { width: 100%; color: #d93025; font-size: 13px; }
</style>
