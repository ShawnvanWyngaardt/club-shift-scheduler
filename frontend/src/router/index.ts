import { createRouter, createWebHistory } from 'vue-router'
import MemberShifts from '@/views/MemberShifts.vue'
import NotFound from '@/views/NotFound.vue'
import CoordinatorLayout from '@/views/CoordinatorLayout.vue'
import OutcomesView from '@/views/OutcomesView.vue'
import ScheduleView from '@/views/ScheduleView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/m/:token', name: 'member', component: MemberShifts, props: true },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFound },
    {
      path: '/c/:clubId/:token',
      component: CoordinatorLayout,
      props: true,
      children: [
        { path: '', name: 'schedule', component: ScheduleView, props: true },
        { path: 'outcomes', name: 'outcomes', component: OutcomesView, props: true },
      ],
    },
  ],
})

export default router
