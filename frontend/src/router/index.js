import { createRouter, createWebHistory } from 'vue-router'

// 1. 引入你的三个核心页面
import WelcomePage from '@/views/WelcomePage.vue'          // 欢迎大门
import LoginPage from '@/views/content/login/LoginPage.vue' // 登录界面
import MainLayout from '@/views/content/MainLayout.vue'     // 整体布局框架
import ChatPage from '@/views/content/chat/ChatPage.vue'    // 真正的聊天大厅

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      // 默认首页：展示发光海螺和气泡
      path: '/',
      name: 'welcome',
      component: WelcomePage
    },
    {
      // 登录页：展示账号密码输入框
      path: '/login',
      name: 'login',
      component: LoginPage
    },
    {
      // 主界面：带侧边栏的布局
      path: '/main',
      name: 'main',
      component: MainLayout,
      redirect: '/main/chat', // 重点：只要来到 /main，就自动帮你推门进入 /main/chat
      children: [
        {
          // 子页面：聊天大厅 (它会被自动塞进 MainLayout 的 router-view 坑位里)
          path: 'chat',
          name: 'chat',
          component: ChatPage
        }
      ]
    }
  ]
})

export default router