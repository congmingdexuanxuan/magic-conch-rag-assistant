package com.spongebob.magic_conch_backend.service;

import com.spongebob.magic_conch_backend.entity.User;

public interface UserService {
    // 注册逻辑
    User register(String username, String password);
    // 登录逻辑
    User login(String username, String password);
}