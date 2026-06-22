import { API_BASE } from './config.js'

export function mediaUrl(path) {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  return API_BASE + path
}
