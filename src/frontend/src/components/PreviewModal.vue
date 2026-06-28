<template>
  <div class="preview-overlay" @click.self="$emit('close')">
    <div class="preview-modal">
      <div class="preview-header">
        <h3>Comment Preview</h3>
        <button class="preview-close" @click="$emit('close')">&times;</button>
      </div>
      <div class="preview-body">
        <div class="preview-author">{{ data.username }}</div>
        <div class="preview-text" v-html="sanitizeHtml(data.text)"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ data: Object })
defineEmits(['close'])

function sanitizeHtml(text) {
  if (!text) return ''
  const tagPattern = /<\/?(\w+)([^>]*)>/g
  const allowedTags = {
    a: ['href', 'title'],
    b: [],
    br: [],
    code: [],
    i: [],
    img: ['src', 'alt', 'width', 'height'],
    p: [],
    strong: [],
  }
  return text.replace(tagPattern, (match, tagName, attrsStr) => {
    const tag = tagName.toLowerCase()
    if (!(tag in allowedTags)) return ''
    if (match.startsWith('</') && tag !== 'img') return match
    if (tag === 'img' || tag === 'br') {
      if (match.startsWith('</')) return ''
      const allowedAttrs = allowedTags[tag]
      const attrPattern = /(\w+)=(["']).*?\2/g
      const cleanAttrs = []
      let m
      while ((m = attrPattern.exec(attrsStr)) !== null) {
        if (allowedAttrs.includes(m[1].toLowerCase())) cleanAttrs.push(m[0])
      }
      return `<${tag}${cleanAttrs.length ? ' ' + cleanAttrs.join(' ') : ''}>`
    }
    const allowedAttrs = allowedTags[tag]
    const attrPattern = /(\w+)=(["']).*?\2/g
    const cleanAttrs = []
    let m
    while ((m = attrPattern.exec(attrsStr)) !== null) {
      if (allowedAttrs.includes(m[1].toLowerCase())) cleanAttrs.push(m[0])
    }
    return `<${tag}${cleanAttrs.length ? ' ' + cleanAttrs.join(' ') : ''}>`
  })
}
</script>

<style scoped>
.preview-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.preview-modal {
  background: #fff; border-radius: 8px; width: 90%; max-width: 600px;
  max-height: 80vh; overflow-y: auto; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.preview-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e0e0e0; }
.preview-header h3 { font-size: 16px; color: #333; margin: 0; }
.preview-close { background: none; border: none; font-size: 24px; cursor: pointer; color: #999; }
.preview-close:hover { color: #333; }
.preview-body { padding: 20px; }
.preview-author { font-weight: 600; color: #1a73e8; margin-bottom: 12px; }
.preview-text { font-size: 14px; line-height: 1.6; color: #333; }
.preview-text :deep(a) { color: #1a73e8; }
.preview-text :deep(code) { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
.preview-text :deep(i) { font-style: italic; }
.preview-text :deep(strong) { font-weight: 700; }
.preview-text :deep(img) { max-width: 100%; border-radius: 4px; }
</style>
