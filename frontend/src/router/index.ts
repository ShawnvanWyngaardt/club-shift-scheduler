import { createRouter, createWebHistory } from 'vue-router'
import MemberShifts from '@/views/MemberShifts.vue'
import NotFound from '@/views/NotFound.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/m/:token', name: 'member', component: MemberShifts, props: true },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFound },
  ],
})

export default router
