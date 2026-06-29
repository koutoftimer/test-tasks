<template>
  <div class="app">
    <div class="container">
      <div class="auth-bar">
        <template v-if="auth.user">
          <span class="auth-user">{{ auth.user.username }}</span>
          <button class="btn-edit-profile" @click="showProfileForm = !showProfileForm">Edit profile</button>
          <button class="btn-logout" @click="handleLogout">Logout</button>
          <div v-if="showProfileForm" class="profile-form">
            <div class="profile-form-fields">
              <label>Email</label>
              <input v-model="profileEmail" type="email" />
              <label>Homepage</label>
              <div class="profile-homepage-wrap">
                <input v-model="profileHomepage" type="url" placeholder="https://" />
                <a v-if="auth.profile?.homepage" :href="auth.profile.homepage" target="_blank" class="profile-homepage-link" title="Open homepage">&#8599;</a>
              </div>
              <label>Avatar</label>
              <div class="profile-avatar-wrap">
                <img v-if="auth.profile?.avatar" :src="auth.profile.avatar" alt="Avatar" class="profile-avatar-preview" />
                <input type="file" accept="image/*" @change="onAvatarChange" />
              </div>
              <div class="profile-form-buttons">
                <button class="btn-save" @click="handleUpdateProfile">Save</button>
                <button class="btn-cancel" @click="showProfileForm = false">Cancel</button>
              </div>
              <div v-if="profileError" class="auth-error">{{ profileError }}</div>
              <div v-if="profileSuccess" class="profile-success">{{ profileSuccess }}</div>
            </div>
          </div>
        </template>
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
import { onMounted, ref, watch } from 'vue'
import { useAuthStore } from './stores/auth.js'
import { resizeAvatar } from './composables/resizeImage.js'
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
const showProfileForm = ref(false)
const profileEmail = ref('')
const profileHomepage = ref('')
const profileAvatar = ref(null)
const profileError = ref('')
const profileSuccess = ref('')

onMounted(() => {
  if (auth.accessToken) {
    auth.fetchUser()
  }
})

watch(() => auth.user, (user) => {
  if (user) {
    profileEmail.value = user.email || ''
  }
})

watch(() => auth.profile, (profile) => {
  if (profile) {
    profileHomepage.value = profile.homepage || ''
  }
}, { immediate: true })

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

function onAvatarChange(e) {
  profileAvatar.value = e.target.files[0] || null
}

async function handleUpdateProfile() {
  profileError.value = ''
  profileSuccess.value = ''
  try {
    const avatarFile = profileAvatar.value ? await resizeAvatar(profileAvatar.value) : null
    await auth.updateProfile({
      email: profileEmail.value,
      homepage: profileHomepage.value,
      avatar: avatarFile,
    })
    profileSuccess.value = 'Profile updated'
    setTimeout(() => { profileSuccess.value = '' }, 3000)
  } catch (err) {
    profileError.value = err.response?.data?.detail || 'Failed to update profile'
  }
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
.btn-edit-profile {
  background: none; border: 1px solid #d0d0d0; color: #555;
  padding: 6px 14px; border-radius: 3px; font-size: 13px;
}
.btn-edit-profile:hover { background: #f5f5f5; }
.profile-form { width: 100%; padding: 12px; background: #f8f9fa; border-radius: 4px; margin-top: 8px; }
.profile-form-fields { display: flex; flex-direction: column; gap: 8px; }
.profile-form-fields label { font-size: 12px; font-weight: 600; color: #555; }
.profile-form-fields input { padding: 6px 10px; border: 1px solid #d0d0d0; border-radius: 3px; font-size: 13px; font-family: inherit; }
.profile-form-fields input:focus { outline: none; border-color: #1a73e8; }
.profile-form-buttons { display: flex; gap: 8px; margin-top: 4px; }
.btn-save {
  background: #1a73e8; color: #fff; border: none; padding: 6px 14px;
  border-radius: 3px; font-size: 13px; font-weight: 500;
}
.btn-save:hover { background: #1557b0; }
.btn-cancel {
  background: none; border: 1px solid #d0d0d0; color: #555;
  padding: 6px 14px; border-radius: 3px; font-size: 13px;
}
.btn-cancel:hover { background: #f5f5f5; }
.profile-success { width: 100%; color: #188038; font-size: 13px; }
.profile-homepage-wrap { display: flex; align-items: center; gap: 6px; }
.profile-homepage-wrap input { flex: 1; }
.profile-homepage-link { font-size: 16px; color: #1a73e8; text-decoration: none; }
.profile-homepage-link:hover { text-decoration: underline; }
.profile-avatar-wrap { display: flex; align-items: center; gap: 10px; }
.profile-avatar-preview { width: 24px; height: 24px; border-radius: 3px; object-fit: cover; }
</style>
