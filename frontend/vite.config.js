import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // 【新增配置 1】：告诉打包工具允许使用最新的 ES 语法
  build: {
    target: 'esnext'
  },
  // 【新增配置 2】：告诉本地开发服务器允许使用最新的 ES 语法
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext'
    }
  }
})