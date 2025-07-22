import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/Home.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/Home.vue'),
    },
    {
      path: '/dialogs',
      name: 'dialogs',
      component: () => import('../views/Dialogs.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/Home.vue'),
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
