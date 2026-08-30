package com.spongebob.magic_conch_backend.controller.chat;

import com.spongebob.magic_conch_backend.common.vo.Result; // 【修复点】：精准引入了你的 Result
import com.spongebob.magic_conch_backend.entity.User;
import com.spongebob.magic_conch_backend.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
@CrossOrigin // 允许跨域请求
public class UserController {

    @Autowired
    private UserService userService;

    // 注册接口
    @PostMapping("/register")
    public Result register(@RequestBody User user) {
        try {
            User newUser = userService.register(user.getUsername(), user.getPassword());
            return Result.success(newUser);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error(); // 【修复点】：使用你原本就有的无参 error 方法
        }
    }

    // 登录接口
    @PostMapping("/login")
    public Result login(@RequestBody User user) {
        try {
            User loginUser = userService.login(user.getUsername(), user.getPassword());
            // 登录成功！把用户信息发给前端
            return Result.success(loginUser);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error(); // 【修复点】：同上
        }
    }
}