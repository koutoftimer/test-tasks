import { createRouter, createWebHistory } from 'vue-router'
import CommentListView from '../views/CommentListView.vue'
import CommentDetailView from '../views/CommentDetailView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const routes = [
  { path: '/', name: 'list', component: CommentListView, props: { pageNum: 1 } },
  { path: '/page/:pageNum(\\d+)', name: 'list-page', component: CommentListView, props: true },
  { path: '/comment/:id', name: 'detail', component: CommentDetailView },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let previousRouteName = null

router.beforeEach((to, from) => {
  previousRouteName = from.name
})

export function wasPreviouslyOnList() {
  return previousRouteName === 'list' || previousRouteName === 'list-page'
}

export default router
