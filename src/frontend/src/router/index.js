import { createRouter, createWebHistory } from 'vue-router'
import CommentListView from '../views/CommentListView.vue'
import CommentDetailView from '../views/CommentDetailView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const routes = [
  { path: '/', name: 'list', component: CommentListView },
  { path: '/comment/:id', name: 'detail', component: CommentDetailView },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
