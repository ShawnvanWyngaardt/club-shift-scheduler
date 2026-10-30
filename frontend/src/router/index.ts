import { createRouter, createWebHistory } from 'vue-router'
import MemberShifts from '@/views/MemberShifts.vue'
import NotFound from '@/views/NotFound.vue'
import CoordinatorLayout from '@/views/CoordinatorLayout.vue'
import LandingView from '@/views/LandingView.vue'
import OutcomesView from '@/views/OutcomesView.vue'
import SetupView from '@/views/SetupView.vue'
import StartClubView from '@/views/StartClubView.vue'
import ScheduleView from '@/views/ScheduleView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: LandingView },
    {
      path: '/start',
      name: 'start',
      component: StartClubView,
      meta: { title: 'Start a club' },
    },
    {
      path: '/m/:token',
      name: 'member',
      component: MemberShifts,
      props: true,
      meta: { title: 'My shifts' },
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFound },
    {
      path: '/c/:clubId/:token',
      component: CoordinatorLayout,
      props: true,
      children: [
        { path: '', name: 'schedule', component: ScheduleView, props: true },
        { path: 'outcomes', name: 'outcomes', component: OutcomesView, props: true },
        { path: 'setup', name: 'setup', component: SetupView, props: true },
      ],
      meta: { title: 'Coordinator' },
    },
  ],
})

router.afterEach((to) => {
  const page = to.meta.title as string | undefined
  document.title = page ? `${page} · Club Shift Scheduler` : 'Club Shift Scheduler'
})

export default router
