import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: '/auth/login',
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/Settings.vue'),
    },
    {
      path: '/dialogs',
      name: 'dialogs',
      component: () => import('../views/Dialogs.vue'),
    },
    {
      path: "/auth/login",
      name: "login",
      component: () => import('../views/auth/Login.vue'),
    },
    {
      path: '/dialogs/:chatId',
      name: 'chat',
      component: () => import('../views/Chat.vue'),
      props: true
    }
  ],
})

export default router
