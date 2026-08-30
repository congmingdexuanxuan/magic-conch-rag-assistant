<template>
  <div class="ai-practice-container">
    <div class="history-panel">
      <div class="new-chat-container">
        <button class="new-chat-btn" @click="newConversation">
          新建对话
          <el-icon class="plus-icon"><Plus/></el-icon>
        </button>
      </div>
      <ul class="history-list">
        <li v-for="(item, index) in historyList" :key="item.id"
            @click="selectConversation(item)"
            :class="{ active: activeSessionId === item.id }">

          <span class="session-title">{{ item.title }}</span>

          <el-icon class="delete-icon" @click.stop="deleteChat(item, index)"><Delete/></el-icon>

        </li>
      </ul>
    </div>

    <div class="chat-wrapper">
      <div class="chat-panel">
        <div class="chat-messages" ref="chatMessagesRef">
          <div v-for="(message, index) in currentMessages" :key="index" :class="['message', message.role]">
            <div class="avatar">
              <div v-if="message.role !== 'user'" class="ai-avatar">
                <img src="@/assets/images/hailuo2.png" alt="AI Avatar">
              </div>
              <div v-else>
                <img src="@/assets/images/user.png" alt="Me">
              </div>
            </div>
            <div class="content" v-html="renderMarkdown(message.content)">
            </div>
          </div>
        </div>

        <div class="input-area">
          <div class="input-wrapper">
            <el-icon class="input-icon link-icon"><Link/></el-icon>
            <input
                v-model="userInput"
                @keyup.enter="sendMessage"
                placeholder="输入消息，按回车发送..."
                type="text"
                :disabled="isInputDisabled"
            >
            <div class="button-group">
              <div class="audio-wave" v-if="isRecording" @click="finishRecording">
                <span v-for="n in 4" :key="n" :style="{ animationDelay: `${n * 0.2}s` }"></span>
              </div>
              <el-icon v-else class="input-icon microphone-icon" @click="toggleRecording">
                <Microphone/>
              </el-icon>
              <div class="separator"></div>
              <el-popover placement="top" :width="200" trigger="hover" :disabled="!!userInput.trim()">
                <template #reference>
                  <el-button class="send-button" circle @click="sendMessage" :disabled="!userInput.trim()">
                    <el-icon><Top/></el-icon>
                  </el-button>
                </template>
                <span>请文字/录音/上传语音回复</span>
              </el-popover>
            </div>
          </div>
        </div>

        <div class="disclaimer">
          服务生成的所有内容均由大聪明本聪明来生成，其生成内容的准确性和完整性无法保证，有可能回答的不对就去自己查资料
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import { Link, Microphone, Plus, Top, Delete } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus'; // <--- 加了 ElMessageBox
import { get } from '@/utils/request';
import { API } from '@/api/config';

// 引入 Markdown 和最新的 MathJax3 渲染工具
import MarkdownIt from 'markdown-it';
import mathjax3 from 'markdown-it-mathjax3';

// 初始化渲染器
const md = new MarkdownIt({ breaks: true }).use(mathjax3);

const renderMarkdown = (text) => {
  if (!text) return '';  //这里为什么要这么写，回答说是为了防止崩溃但是我我还是没懂
  return md.render(text);
};

// ====== 核心记忆状态 ======
const historyList = ref([]); //历史聊天记录
const activeSessionId = ref(null);
const currentMessages = ref([
  { role: 'assistant', content: '您好！我是大聪明，你问我的问题有可能我不会，不会的你就自己去查资料' }
]);

const userInput = ref('');
const chatMessagesRef = ref(null);
const isRecording = ref(false);
let mediaRecorder = null;
const mediaStream = ref(null);
const isInputDisabled = ref(false);

// 1. 获取左侧列表
const fetchSessionList = async () => {
  try {
    // 【关键】：把管家手里记的 userId 传给后端
    const res = await get('/chat/sessions', { userId: userStore.userId });
    if (res.code == 100 || res.code == 200) {
      historyList.value = res.data;
    }
  } catch (error) {
    console.error('拉取历史列表失败', error);
  }
};

// 2. 点击左侧切换聊天
const selectConversation = async (item) => {
  activeSessionId.value = item.id;
  try {
    const res = await get('/chat/history?sessionId=' + item.id);
    if (res.code == 100 || res.code == 200) {
      if(res.data.length === 0) {
        currentMessages.value = [{ role: 'assistant', content: '您好！我是大聪明...' }];
      } else {
        currentMessages.value = res.data;
      }
      nextTick(() => scrollToBottom());
    }
  } catch (error) {
    ElMessage.error('获取聊天记录失败');
  }
};

// 3. 新建对话
const newConversation = () => {
  activeSessionId.value = null;
  currentMessages.value = [
    { role: 'assistant', content: '您好！我是大聪明，有什么新问题吗？' }
  ];
};

// 4. 发送消息
const sendMessage = async () => {
  if (userInput.value.trim()) {
    const prompt = userInput.value;
    currentMessages.value.push({ role: 'user', content: prompt });
    userInput.value = '';
    nextTick(() => scrollToBottom());

    // 塞入一个大聪明正在思考的占位符
    const loadingObj = { role: 'assistant', content: '大聪明正在思考...', loading: true };
    currentMessages.value.push(loadingObj);
    nextTick(() => scrollToBottom());

    try {
      const payload = {
        prompt: prompt,
        userId: userStore.userId // 【关键】：告诉后端是谁在提问
      };
      if (activeSessionId.value) {
        payload.sessionId = activeSessionId.value;
      }

      const res = await get(API.GENERATE, payload);

      if (res.code == 100 || res.code == 200) {
        // 找到最后一条消息（也就是正在思考那条）
        const lastMsg = currentMessages.value[currentMessages.value.length - 1];

        // 兼容处理：如果后端直接返了字符串，或者返了大礼包
        if (typeof res.data === 'string') {
          lastMsg.content = res.data;
        } else {
          lastMsg.content = res.data.answer;
          // 如果这是一个全新的对话，把新生成的 ID 记下来，并刷新左侧列表
          if (!activeSessionId.value && res.data.sessionId) {
            activeSessionId.value = res.data.sessionId;
            fetchSessionList();
          }
        }
        lastMsg.loading = false;
        nextTick(() => scrollToBottom());
      } else {
        ElMessage.error(res.msg || '获取回复失败');
        currentMessages.value[currentMessages.value.length - 1].content = '获取回复失败，请稍后重试';
      }
    } catch (error) {
      console.error(error);
      currentMessages.value[currentMessages.value.length - 1].content = '获取回复失败，请检查网络';
    }
  }
};
// 5. 删除对话
const deleteChat = (item, index) => {
  ElMessageBox.confirm('确定要让大聪明忘掉这段对话吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '算了',
    type: 'warning',
  }).then(async () => {
    try {
      // 调用后端的删除接口
      const res = await get('/chat/deleteSession?sessionId=' + item.id);
      if (res.code == 100 || res.code == 200) {
        ElMessage.success('大聪明已经清除了这段记忆！');

        // 关键1：把前端列表里的这个元素抽掉（页面瞬间消失）
        historyList.value.splice(index, 1);

        // 关键2：如果删掉的正好是右边正在看的对话，就把右边清空，变成新建对话的状态
        if (activeSessionId.value === item.id) {
          newConversation();
        }
      } else {
        ElMessage.error('删除失败了');
      }
    } catch (error) {
      console.error(error);
    }
  }).catch(() => {
    // 点取消就不管它
  });
};

import { useUserStore } from '@/store/user';
const userStore = useUserStore(); // 获取当前用户信息
// 滚动到底部
const scrollToBottom = () => {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
  }
};

// 录音相关保留原样
const finishRecording = () => {
  if (isRecording.value && mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    isRecording.value = false;
    isInputDisabled.value = false;
  }
};

const toggleRecording = async () => {};

const stopMediaStream = () => {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop());
    mediaStream.value = null;
  }
};

onMounted(() => {
  fetchSessionList();
});

onUnmounted(() => {
  finishRecording();
  stopMediaStream();
});
</script>

<style scoped>
/* 样式保持不变 */
.ai-practice-container {
  display: flex;
  height: 100vh;
  font-family: Arial, sans-serif;
}

.history-panel {
  width: 280px;
  background: linear-gradient(135deg, rgba(230, 240, 255, 0.01), rgba(240, 230, 255, 0.01));
  background-color: #ffffff;
  padding: 20px;
  overflow-y: auto;
}

.new-chat-container {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 13px; /* 略微增加内边距 */
  margin-top: 10px;
  margin-bottom: 5px;
  background: linear-gradient(to right, #0069e0, #0052bc); /* 改用更深的蓝色渐变 */
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.3s;
  font-size: 14px; /* 加大字号 */
  font-weight: bold; /* 加粗字体 */
}

.new-chat-btn:hover {
  opacity: 0.9;
}

.history-list {
  list-style-type: none;
  padding: 0;
}

.history-list li {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #ffffff;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;

  /* 【新增 Flex 布局】，让文字和图标一左一右同行显示 */
  display: flex;
  justify-content: space-between;
  align-items: center;
}
/* 限制标题过长自动变成省略号 */
.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 10px;
}

/* 垃圾桶图标默认隐藏，颜色是浅灰色 */
.delete-icon {
  color: #999;
  font-size: 16px;
  display: none;
}

/* 鼠标放到整个方块上时，垃圾桶才显示出来 */
.history-list li:hover .delete-icon {
  display: block;
}

/* 鼠标悬停在垃圾桶上时，变成危险的红色 */
.delete-icon:hover {
  color: #ff4d4f;
  transform: scale(1.1);
}
.history-list li:hover,
.history-list li.active {
  background-color: rgba(0, 105, 224, 0.15);
  color: #0052bc;
}

.chat-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg,
  rgba(0, 105, 224, 0.08),
  rgba(0, 56, 148, 0.08)
  );
}

.chat-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent;
  box-shadow: none;
  padding-top: 12px; /* 添加顶部内边距 */
  /* padding-left: 10%;
  padding-right: 10%; */
}

.visitor-info {
  background-color: transparent; /* 背透明 */
  padding: 15px 20px; /* 增加内边距 */
  margin-bottom: 20px; /* 增加与第一条对话的距离 */
  font-weight: bold;
  color: #333;
  text-align: left;
  font-size: 18px; /* 增大字体大小 */
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding-top: 20px;
  padding-left: 10%;
  padding-right: 10%;
  background-color: transparent;
  /* 修改滚动条颜色 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 105, 224, 0.3) transparent;
}

/* 为 Webkit 浏览器（如 Chrome、Safari）自定义滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: rgba(0, 105, 224, 0.3);
  border-radius: 3px;
}

.message {
  display: flex;
  margin-bottom: 20px;
}

.message .avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  overflow: hidden;
}

.message .avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
}

.message .content {
  background-color: rgba(255, 255, 255, 1);
  color: #333333; /* 【关键修复 1】：强制把文字变成深灰色，防止和白背景融为一体 */
  padding: 12px 18px;
  border-radius: 10px;
  max-width: 80%;
  font-size: 16px;
  line-height: 1.8;
  overflow-x: auto; /* 【关键修复 2】：数学公式有时候很长，这行代码能保证公式太长时可以左右滑动，而不会撑破气泡 */
}

.message.user {
  flex-direction: row-reverse;
}

.message.user .avatar {
  margin-right: 0;
  margin-left: 10px;
}

.message.user .content {
  background-color: rgba(0, 105, 224, 0.12);
  color: black;
}

.input-area {
  padding: 20px 10% 0 10%;
  border-top: 0px solid #e0e0e0;
  background-color: transparent;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

input {
  width: 100%;
  padding: 12px 110px 12px 50px; /* 调整右侧padding以适应新的按钮组 */
  border: 1px solid rgba(204, 204, 204, 0.5);
  border-radius: 25px;
  font-size: 16px;
  background-color: rgba(255, 255, 255, 0.7);
  transition: border-color 0.3s;
  height: 55px;
}

input:focus {
  outline: none;
  border-color: #0069e0;
}

input::placeholder {
  color: #969696;
}

.button-group {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
}

.input-icon {
  color: #0069e0;
  font-size: 24px;
  cursor: pointer;
}

.link-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
}

.microphone-icon {
  margin-right: 0; /* 将右侧边距改为0 */
}

.separator {
  width: 1px;
  height: 25px;
  background-color: rgba(204, 204, 204, 0.5);
  margin: 0 10px;
}

.send-button {
  width: 40px;
  height: 40px;
  background: linear-gradient(to right, #0069e0, #0052bc); /* 保持一致的蓝色渐变 */
  border: none;
  color: white;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.send-button:disabled {
  background: rgba(0, 105, 224, 0.1);
  color: rgba(0, 82, 188, 0.3);
  cursor: default;
}

.send-button :deep(.el-icon) {
  font-size: 24px;
}

.send-button:not(:disabled):hover {
  opacity: 0.9;
}

/* 新增的免责声明样式 */
.disclaimer {
  font-size: 10px;
  color: #999;
  text-align: center;
  margin-top: 12px;
  margin-bottom: 12px;
}

.audio-wave {
  display: flex;
  align-items: center;
  height: 24px;
  width: 24px;
}

.audio-wave span {
  display: inline-block;
  width: 3px;
  height: 100%;
  margin-right: 1px;
  background: #0069e0;
  animation: audio-wave 0.8s infinite ease-in-out;
}

@keyframes audio-wave {
  0%, 100% {
    transform: scaleY(0.3);
  }
  50% {
    transform: scaleY(1);
  }
}

.message .content audio {
  margin-top: 10px;
  width: 100%;
}
/* 让 v-html 渲染出来的段落去掉多余的边距 */
.message .content :deep(p) {
  margin: 0 0 8px 0;
}
.message .content :deep(p:last-child) {
  margin-bottom: 0;
}

</style>