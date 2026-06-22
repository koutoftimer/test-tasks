import axios from 'axios'
import { defineStore } from 'pinia'

const API_BASE = 'http://api.comments:8002'

const api = axios.create({
  baseURL: API_BASE + '/api',
})

export const useCommentStore = defineStore('comment', {
  state: () => ({
    comments: [],
    total: 0,
    page: 1,
    totalPages: 1,
    sortBy: '-created_at',
    loading: false,
    error: null,
    captchaKey: '',
    captchaUrl: '',
    showForm: false,
    lightboxImage: null,
    previewData: null,
  }),

  actions: {
    async fetchComments() {
      this.loading = true
      this.error = null
      try {
        const response = await api.get('/comments/', {
          params: { page: this.page, sort: this.sortBy },
        })
        this.comments = response.data.results || []
        this.total = response.data.count || 0
        this.totalPages = Math.ceil(this.total / 25)
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to load comments'
      } finally {
        this.loading = false
      }
    },

    async fetchComment(id) {
      const response = await api.get(`/comments/${id}/`)
      return response.data
    },

    async createComment(data) {
      const formData = new FormData()
      formData.append('username', data.username)
      formData.append('email', data.email)
      formData.append('text', data.text)
      formData.append('captcha_key', data.captcha_key)
      formData.append('captcha_value', data.captcha_value)
      if (data.homepage) formData.append('homepage', data.homepage)
      if (data.parent_id) formData.append('parent_id', String(data.parent_id))
      if (data.file) formData.append('file', data.file)

      try {
        const response = await api.post('/comments/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        return response.data
      } catch (err) {
        if (err.response?.data) {
          const detail = typeof err.response.data === 'string'
            ? err.response.data
            : Object.values(err.response.data).flat().join(', ')
          throw new Error(detail || 'Failed to create comment')
        }
        throw new Error('Network error')
      }
    },

    async fetchCaptcha() {
      try {
        const response = await api.get('/captcha/')
        const data = response.data
        data.image_url = API_BASE + data.image_url
        return data
      } catch (err) {
        throw new Error('Failed to load CAPTCHA')
      }
    },

    async refreshCaptchaKey() {
      try {
        const data = await this.fetchCaptcha()
        this.captchaKey = data.key
        this.captchaUrl = data.image_url
      } catch {
        // ignore
      }
    },

    setSort(field) {
      if (this.sortBy === field) {
        this.sortBy = `-${field}`
      } else {
        this.sortBy = field
      }
      this.page = 1
      this.fetchComments()
    },

    goToPage(p) {
      this.page = p
      this.fetchComments()
    },

    handleCommentCreated(comment) {
      this.showForm = false
      this.comments.unshift(comment)
      this.refreshCaptchaKey()
    },

    addReply(parentId, reply) {
      const findParent = (items) => {
        for (const item of items) {
          if (item.id === parentId) {
            item.replies.push(reply)
            return
          }
          if (item.replies && item.replies.length) {
            findParent(item.replies)
          }
        }
      }
      findParent(this.comments)
    },

    openLightbox(url) {
      this.lightboxImage = url
    },

    closeLightbox() {
      this.lightboxImage = null
    },

    openPreview(data) {
      this.previewData = data
    },

    closePreview() {
      this.previewData = null
    },
  },
})
