<template>
  <div class="login-container">
    <div class="glass-card">
      <div class="card-header">
        <img src="@/assets/images/hailuo.png" alt="logo" class="logo-img">
        <h2>{{ isLogin ? '召唤大聪明' : '注册大聪明' }}</h2>
        <p class="subtitle">{{ isLogin ? '欢迎回来，我的朋友！' : '注册一个专属的大聪明为你服务吧！' }}</p>
      </div>

      <div class="form-body">
        <el-input
            v-model="formData.username"
            placeholder="请输入账号 "
            class="custom-input"
            size="large">
          <template #prefix>
            <el-icon><User /></el-icon>
          </template>
        </el-input>

        <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入暗号 "
            show-password
            class="custom-input"
            size="large">
          <template #prefix>
            <el-icon><Lock /></el-icon>
          </template>
        </el-input>

        <el-button
            class="submit-btn"
            type="primary"
            size="large"
            @click="handleSubmit">
          {{ isLogin ? '立即召唤' : '立即注册' }}
        </el-button>

        <div class="toggle-text">
          <span v-if="isLogin">还没有账号？ <a @click="isLogin = false">立即注册</a></span>
          <span v-else>已经有账号了？ <a @click="isLogin = true">去登录</a></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { User, Lock } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/store/user'; // 【新增】：唤醒管家
import { post } from '@/utils/request';      // 【新增】：引入发起 POST 请求的工具

const router = useRouter();
const userStore = useUserStore(); // 实例化管家

// 控制当前是“登录”界面还是“注册”界面
const isLogin = ref(true);

// 收集用户输入的数据
const formData = ref({
  username: '',
  password: ''
});

// 点击提交按钮
const handleSubmit = async () => {
  if (!formData.value.username || !formData.value.password) {
    ElMessage.warning('账号和暗号都不能为空哦！');
    return;
  }

  if (isLogin.value) {
    // ==================== 登录逻辑 ====================
    try {
      const res = await post('/user/login', formData.value);
      if (res.code == 100 || res.code == 200) {
        ElMessage.success('召唤成功！欢迎回到比奇堡！');

        // 【核心步骤】：把用户信息交给管家保管！
        // 因为我们暂时还没做 JWT Token，所以先用一段假暗号代替 token，并存下真实的用户名
        userStore.setLoginInfo('magic_token_666', res.data.username, res.data.id);

        // 门卫放行，跳转到聊天大厅！
        router.push('/main/chat');
      } else {
        ElMessage.error('召唤失败：' + (res.msg || '账号或暗号不对哦'));
      }
    } catch (error) {
      console.error(error);
      ElMessage.error('网络开了个小差，请稍后再试');
    }
  } else {
    // ==================== 注册逻辑 ====================
    try {
      const res = await post('/user/register', formData.value);
      if (res.code == 100 || res.code == 200) {
        ElMessage.success('办理入住成功！快去大聪明吧！');
        // 注册成功后，清空密码，自动切回登录状态
        formData.value.password = '';
        isLogin.value = true;
      } else {
        ElMessage.error('注册失败：' + (res.msg || '可能是名字被抢注啦'));
      }
    } catch (error) {
      console.error(error);
      ElMessage.error('网络开了个小差，请稍后再试');
    }
  }
};
</script>

<style scoped>
/* 全屏背景图设置 */
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  /* 这里换成你截图中那张带海绵宝宝和派大星的高清背景图的路径！ */
  background-image: url('@/assets/images/loginbackground.png');
  background-size: cover;
  background-position: center;
  position: relative;
}

/* 加一层暗色遮罩，让中间的卡片更突出 */
.login-container::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
}

/* 核心：高级毛玻璃卡片 */
.glass-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: 40px;
  border-radius: 20px;
  /* 毛玻璃魔法代码 */
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);

  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-img {
  width: 80px;
  margin-bottom: 10px;
  filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.3));
}

.card-header h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
  letter-spacing: 2px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #e0e0e0;
}

.form-body {
  width: 100%;
}

/* 深度修改 Element Plus 输入框的默认样式，让它也变透明 */
.custom-input {
  margin-bottom: 20px;
}
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.2) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  border-radius: 10px;
}
:deep(.el-input__inner) {
  color: white !important;
}
:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.7);
}
:deep(.el-icon) {
  color: white;
}

/* 渐变色提交按钮 */
.submit-btn {
  width: 100%;
  border-radius: 10px;
  font-size: 18px;
  font-weight: bold;
  border: none;
  background: linear-gradient(135deg, #00b4db, #0083b0);
  box-shadow: 0 4px 15px rgba(0, 180, 219, 0.4);
  transition: all 0.3s ease;
  margin-top: 10px;
}
.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 180, 219, 0.6);
}

.toggle-text {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
}
.toggle-text a {
  color: #00b4db;
  font-weight: bold;
  cursor: pointer;
  text-decoration: underline;
  transition: color 0.3s;
}
.toggle-text a:hover {
  color: #0083b0;
}
</style>