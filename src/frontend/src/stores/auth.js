import axios from 'axios'
import { defineStore } from 'pinia'

const API_BASE = 'http://api.comments:8002'

const authApi = axios.create({
  baseURL: API_BASE + '/api',
})

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    profileId: null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
  },

  actions: {
    setTokens(access, refresh) {
      this.accessToken = access
      this.refreshToken = refresh
      localStorage.setItem('access_token', access)
      if (refresh) localStorage.setItem('refresh_token', refresh)
    },

    clearTokens() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.profileId = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },

    async register(username, email, password) {
      await authApi.post('/auth/users/', { username, email, password })
    },

    async login(username, password) {
      const res = await authApi.post('/auth/jwt/create/', { username, password })
      this.setTokens(res.data.access, res.data.refresh)
      await this.fetchUser()
    },

    async fetchUser() {
      if (!this.accessToken) return
      try {
        const res = await authApi.get('/auth/users/me/', {
          headers: { Authorization: `Bearer ${this.accessToken}` },
        })
        this.user = res.data
        this.profileId = res.data.profile_id
      } catch {
        this.clearTokens()
      }
    },

    logout() {
      this.clearTokens()
    },

    async updateProfile(data) {
      const formData = new FormData()
      if (data.email !== undefined) formData.append('email', data.email)
      if (data.homepage !== undefined) formData.append('homepage', data.homepage)
      if (data.avatar) formData.append('avatar', data.avatar)

      const res = await authApi.patch(`/profile/${this.profileId}/`, formData, {
        headers: {
          Authorization: `Bearer ${this.accessToken}`,
          'Content-Type': 'multipart/form-data',
        },
      })
      if (this.user && res.data.email !== undefined) {
        this.user.email = res.data.email
      }
      return res.data
    },
  },
})
