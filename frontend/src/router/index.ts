import { createRouter, createWebHistory } from 'vue-router'
import MemberAssignments from '@/views/MemberAssignments.vue'
import MemberLayout from '@/views/MemberLayout.vue'
import MemberShifts from '@/views/MemberShifts.vue'
import MemberStandings from '@/views/MemberStandings.vue'
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
      component: MemberLayout,
      props: true,
      meta: { title: 'My shifts' },
      children: [
        { path: '', name: 'member', component: MemberShifts, props: true },
        {
          path: 'assignments',
          name: 'member-assignments',
          component: MemberAssignments,
          props: true,
        },
        { path: 'standings', name: 'member-standings', component: MemberStandings, props: true },
      ],
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
