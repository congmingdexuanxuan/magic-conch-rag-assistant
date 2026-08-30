import './assets/main.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import VueAudio from 'vue-audio-better'
import { createPinia } from 'pinia' // 【新增1】：把管家公司引进来

const app = createApp(App)
const pinia = createPinia() // 【新增2】：创建一个具体的管家实例

// 全局注册 Element Plus 图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia) // 【新增3】：让整个应用都用上这位管家（建议放在 router 前面）
app.use(VueAudio)
app.use(ElementPlus)
app.use(router)
app.mount('#app')