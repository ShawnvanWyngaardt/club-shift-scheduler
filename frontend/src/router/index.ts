import { createRouter, createWebHistory } from 'vue-router'
import MemberAssignments from '@/views/MemberAssignments.vue'
import MemberLayout from '@/views/MemberLayout.vue'
import MemberShifts from '@/views/MemberShifts.vue'
import MemberStandings from '@/views/MemberStandings.vue'
import NotFound from '@/views/NotFound.vue'
import CheckInView from '@/views/CheckInView.vue'
import CoordinatorLayout from '@/views/CoordinatorLayout.vue'
import LandingView from '@/views/LandingView.vue'
import MembersView from '@/views/MembersView.vue'
import OverviewView from '@/views/OverviewView.vue'
import StartClubView from '@/views/StartClubView.vue'
import WeekView from '@/views/WeekView.vue'

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
        { path: '', name: 'overview', component: OverviewView, props: true },
        { path: 'week/:week', name: 'week', component: WeekView, props: true },
        { path: 'check-in', name: 'check-in', component: CheckInView, props: true },
        // The old address, in case someone kept it
        { path: 'outcomes', redirect: (to) => ({ name: 'check-in', params: to.params }) },
        { path: 'members', name: 'members', component: MembersView, props: true },
        // Old addresses, in case someone kept them. Points now live on Members.
        { path: 'setup', redirect: (to) => ({ name: 'members', params: to.params }) },
        { path: 'points', redirect: (to) => ({ name: 'members', params: to.params }) },
      ],
      meta: { title: 'Coordinator' },
    },
  ],
})

router.afterEach((to) => {
  const page = to.meta.title as string | undefined
  document.title = page ? `${page} | Club Shift Scheduler` : 'Club Shift Scheduler'
})

export default router
