import axios from 'axios'
import { defineStore } from 'pinia'
import { API_BASE } from '../utils/config.js'

const api = axios.create({
  baseURL: API_BASE + '/api',
})

let isRefreshing = false
let pendingRequests = []

api.interceptors.request.use(async (config) => {
  const { useAuthStore } = await import('./auth.js')
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (
      error.response?.status === 401 &&
      error.response?.data?.code === 'token_not_valid' &&
      !originalRequest._retry
    ) {
      const { useAuthStore } = await import('./auth.js')
      const auth = useAuthStore()

      if (!auth.refreshToken) {
        auth.clearTokens()
        delete originalRequest.headers.Authorization
        return api(originalRequest)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push({ resolve })
        }).then((token) => {
          if (token) {
            originalRequest.headers.Authorization = `Bearer ${token}`
          } else {
            delete originalRequest.headers.Authorization
          }
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const res = await axios.post(API_BASE + '/api/auth/jwt/refresh/', {
          refresh: auth.refreshToken,
        })
        const newToken = res.data.access
        auth.setTokens(newToken, auth.refreshToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        pendingRequests.forEach((p) => p.resolve(newToken))
        pendingRequests = []
        return api(originalRequest)
      } catch {
        auth.clearTokens()
        delete originalRequest.headers.Authorization
        pendingRequests.forEach((p) => p.resolve(null))
        pendingRequests = []
        return api(originalRequest)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export const useCommentStore = defineStore('comment', {
  state: () => ({
    comments: [],
    total: 0,
    page: 1,
    totalPages: 1,
    sortBy: '-created_at',
    loading: false,
    error: null,
    showForm: false,
    lightboxImage: null,
    previewData: null,
    currentComment: null,
    currentLoading: false,
    currentError: null,
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

    async fetchReplies(id) {
      const response = await api.get(`/comments/${id}/replies/`)
      return response.data
    },

    async fetchCommentDetail(id) {
      this.currentLoading = true
      this.currentError = null
      try {
        const [commentData, replies] = await Promise.all([
          this.fetchComment(id),
          this.fetchReplies(id),
        ])
        commentData.replies = replies
        this.currentComment = commentData
      } catch (err) {
        this.currentError = err.message || 'Failed to load comment'
      } finally {
        this.currentLoading = false
      }
    },

    async createComment(data) {
      try {
        const response = await api.post('/comments/', data)
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

    async uploadAttachment(file) {
      const formData = new FormData()
      formData.append('file', file)
      try {
        const response = await api.post('/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        return response.data
      } catch (err) {
        if (err.response?.data) {
          const detail = typeof err.response.data === 'string'
            ? err.response.data
            : Object.values(err.response.data).flat().join(', ')
          throw new Error(detail || 'Failed to upload file')
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
      comment.reply_count = comment.replies?.length ?? 0
      this.comments.unshift(comment)
    },

    addReply(parentId, reply) {
      const addTo = (item) => {
        if (!item.replies) item.replies = []
        item.replies.push(reply)
        if (item.reply_count !== undefined) item.reply_count++
      }

      const findParent = (items) => {
        for (const item of items) {
          if (item.id === parentId) {
            addTo(item)
            return true
          }
          if (item.replies?.length) {
            if (findParent(item.replies)) return true
          }
        }
        return false
      }

      findParent(this.comments)

      if (this.currentComment?.id === parentId) {
        addTo(this.currentComment)
      }
    },

    async voteComment(commentId, voteType) {
      const response = await api.post(`/comments/${commentId}/vote/`, { vote: voteType })
      return response.data
    },

    async removeVote(commentId) {
      const response = await api.delete(`/comments/${commentId}/vote/`)
      return response.data
    },

    openLightbox(url) {
      this.lightboxImage = url
    },

    closeLightbox() {
      this.lightboxImage = null
    },

    async sanitizeHtml(text) {
      const response = await api.post('/sanitize/', { text })
      return response.data.text
    },

    openPreview(data) {
      this.previewData = data
    },

    closePreview() {
      this.previewData = null
    },

    refreshCurrentDetail() {
      if (this.currentComment) {
        this.fetchCommentDetail(this.currentComment.id)
      }
    },
  },
})
