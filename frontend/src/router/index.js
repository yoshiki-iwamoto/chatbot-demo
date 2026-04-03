import { createRouter, createWebHistory } from 'vue-router'

const LoginView = () => import('../views/LoginView.vue')
const AppLayout = () => import('../views/AppLayout.vue')
const DashboardView = () => import('../views/DashboardView.vue')
const FAQView = () => import('../views/FAQView.vue')
const ChatHistoryView = () => import('../views/ChatHistoryView.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { guest: true },
  },
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: DashboardView,
      },
      {
        path: 'faqs',
        name: 'FAQs',
        component: FAQView,
      },
      {
        path: 'chat-history',
        name: 'ChatHistory',
        component: ChatHistoryView,
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.matched.some((record) => record.meta.requiresAuth) && !token) {
    next('/login')
  } else if (to.matched.some((record) => record.meta.guest) && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
