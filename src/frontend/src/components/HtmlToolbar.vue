<template>
  <div class="html-toolbar">
    <button type="button" title="Italic" @click="$emit('insert', 'i')"><i>I</i></button>
    <button type="button" title="Strong" @click="$emit('insert', 'strong')"><strong>B</strong></button>
    <button type="button" title="Code" @click="$emit('insert', 'code')"><code>code</code></button>
    <button type="button" title="Link" @click="$emit('insert', 'a')">link</button>
  </div>
</template>

<script setup>
defineEmits(['insert'])
</script>

<style scoped>
.html-toolbar { display: flex; gap: 4px; margin-bottom: 6px; }
.html-toolbar button {
  padding: 4px 10px; border: 1px solid #d0d0d0; background: #fafafa;
  border-radius: 3px; font-size: 13px; cursor: pointer; font-family: inherit;
}
.html-toolbar button:hover { background: #e8e8e8; }
</style>
