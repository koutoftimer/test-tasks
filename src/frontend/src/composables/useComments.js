import axios from 'axios'
import { ref } from 'vue'

const API_BASE = 'http://api.comments:8002'

const api = axios.create({
  baseURL: API_BASE + '/api',
})

export function useComments() {
  const comments = ref([])
  const total = ref(0)
  const page = ref(1)
  const totalPages = ref(1)
  const sortBy = ref('-created_at')
  const loading = ref(false)
  const error = ref(null)

  async function fetchComments() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/comments/', {
        params: { page: page.value, sort: sortBy.value },
      })
      comments.value = response.data.results || []
      total.value = response.data.count || 0
      totalPages.value = Math.ceil(total.value / 25)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load comments'
    } finally {
      loading.value = false
    }
  }

  async function createComment(data) {
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
  }

  async function fetchCaptcha() {
    try {
      const response = await api.get('/captcha/')
      const data = response.data
      data.image_url = API_BASE + data.image_url
      return data
    } catch (err) {
      throw new Error('Failed to load CAPTCHA')
    }
  }

  function setSort(field) {
    if (sortBy.value === field) {
      sortBy.value = `-${field}`
    } else {
      sortBy.value = field
    }
    page.value = 1
    fetchComments()
  }

  function goToPage(p) {
    page.value = p
    fetchComments()
  }

  return {
    comments,
    total,
    page,
    totalPages,
    sortBy,
    loading,
    error,
    fetchComments,
    createComment,
    fetchCaptcha,
    setSort,
    goToPage,
  }
}
