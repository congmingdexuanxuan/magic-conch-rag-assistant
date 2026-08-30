<template>
  <router-view></router-view>
</template>

<script setup>
// 这里什么都不用写，让它保持最干净的状态
</script>

<style>
/* 清楚默认的内外边距，让你的全屏背景图能完美贴合浏览器边缘 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
}
#app {
  height: 100%;
  width: 100%;
}
</style>