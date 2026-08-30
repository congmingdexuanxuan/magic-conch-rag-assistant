package com.spongebob.magic_conch_backend.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.spongebob.magic_conch_backend.entity.User;
import com.spongebob.magic_conch_backend.mapper.UserMapper;
import com.spongebob.magic_conch_backend.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Date;

@Service
public class UserServiceImpl implements UserService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public User register(String username, String password) {
        // 1. 先查查这个名字是不是被别人注册了
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", username);
        if (userMapper.selectCount(queryWrapper) > 0) {
            throw new RuntimeException("这个神奇海螺已经被别人领走啦！换个名字吧！");
        }

        // 2. 没被注册，就新建一个用户存进数据库
        User newUser = new User();
        newUser.setUsername(username);
        newUser.setPassword(password);
        newUser.setCreateTime(new Date());
        userMapper.insert(newUser);

        return newUser;
    }

    @Override
    public User login(String username, String password) {
        // 1. 去数据库里找账号密码都匹配的人
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", username).eq("password", password);
        User user = userMapper.selectOne(queryWrapper);

        if (user == null) {
            throw new RuntimeException("账号或暗号不对哦，神奇海螺拒绝召唤！");
        }
        return user;
    }
}