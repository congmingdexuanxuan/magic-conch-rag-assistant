import { defineStore } from 'pinia'
import { ref } from 'vue'

// 定义一个叫 user 的数据仓库
export const useUserStore = defineStore('user', () => {
    // 1. 记录用户的 Token（门禁卡）
    const token = ref(localStorage.getItem('magic_token') || '')
    // 2. 记录用户的名字
    const username = ref(localStorage.getItem('magic_username') || '')

    // 【关键修复 1】：必须先声明 userId 盒子！
    const userId = ref(localStorage.getItem('magic_userId') || '')

    // 3. 登录成功后，管家会调用这个方法把信息存起来
    const setLoginInfo = (newToken, newUsername, newUserId) => {
        token.value = newToken
        username.value = newUsername
        userId.value = newUserId; // 现在这里不会报错了！

        // 顺便存到浏览器的硬盘里，这样刷新网页也不会掉线！
        localStorage.setItem('magic_token', newToken)
        localStorage.setItem('magic_username', newUsername)
        localStorage.setItem('magic_userId', newUserId);
    }

    // 4. 退出登录时，管家撕掉这一页记录
    const logout = () => {
        token.value = ''
        username.value = ''
        userId.value = ''
        localStorage.removeItem('magic_token')
        localStorage.removeItem('magic_username')
        localStorage.removeItem('magic_userId')
    }

    // 【关键修复 2】：必须把 userId return 出去给别人用！
    return { token, username, userId, setLoginInfo, logout }
})