const MAX_W = 320
const MAX_H = 240

export function resizeImage(file) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      if (img.width <= MAX_W && img.height <= MAX_H) {
        resolve(file)
        return
      }
      const ratio = Math.min(MAX_W / img.width, MAX_H / img.height)
      const w = Math.round(img.width * ratio)
      const h = Math.round(img.height * ratio)
      const canvas = document.createElement('canvas')
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(img, 0, 0, w, h)
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error('Failed to resize image'))
          return
        }
        const resized = new File([blob], file.name, {
          type: file.type,
          lastModified: Date.now(),
        })
        resolve(resized)
      }, file.type)
    }
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = URL.createObjectURL(file)
  })
}
