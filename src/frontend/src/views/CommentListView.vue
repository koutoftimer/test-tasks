<template>
  <div>
    <h1>Comments</h1>
    <button v-if="!store.showForm" class="btn-leave-comment" @click="store.showForm = true">
      Leave a comment
    </button>
    <CommentForm
      v-if="store.showForm"
      @comment-created="store.handleCommentCreated($event)"
      @cancel="store.showForm = false"
    />
    <SortControls
      :sort-by="store.sortBy"
      @sort="handleSort"
    />
    <CommentList
      :comments="store.comments"
      :loading="store.loading"
      :error="store.error"
      :show-replies="false"
      @select="goToDetail"
    />
    <Pagination
      :page="Number(pageNum)"
      :total-pages="store.totalPages"
      @go-to-page="handleGoToPage"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCommentStore } from '../stores/comment.js'
import CommentForm from '../components/CommentForm.vue'
import CommentList from '../components/CommentList.vue'
import SortControls from '../components/SortControls.vue'
import Pagination from '../components/Pagination.vue'

const DEFAULT_SORT = '-created_at'

const props = defineProps({ pageNum: { type: Number, default: 1 } })
const store = useCommentStore()
const route = useRoute()
const router = useRouter()

onMounted(() => {
  store.page = Number(props.pageNum)
  if (route.query.sort && route.query.sort !== store.sortBy) {
    store.sortBy = route.query.sort
  }
  store.fetchComments()
})

function handleSort(field) {
  if (store.sortBy === field) {
    store.sortBy = `-${field}`
  } else {
    store.sortBy = field
  }

  const page = Number(props.pageNum)
  const query = store.sortBy !== DEFAULT_SORT ? { sort: store.sortBy } : {}

  if (page > 1) {
    router.replace({ name: 'list-page', params: { pageNum: page }, query })
  } else {
    router.replace({ name: 'list', query })
  }
}

function handleGoToPage(p) {
  const query = {}
  if (route.query.sort && route.query.sort !== DEFAULT_SORT) {
    query.sort = route.query.sort
  }
  router.push({ name: 'list-page', params: { pageNum: Number(p) }, query })
}

function goToDetail(comment) {
  router.push({ name: 'detail', params: { id: comment.id } })
}
</script>

<style scoped>
h1 {
  font-size: 24px;
  margin-bottom: 24px;
  color: #1a1a2e;
}

.btn-leave-comment {
  display: block;
  margin-bottom: 16px;
  background: #1a73e8;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}
.btn-leave-comment:hover {
  background: #1557b0;
}
</style>
