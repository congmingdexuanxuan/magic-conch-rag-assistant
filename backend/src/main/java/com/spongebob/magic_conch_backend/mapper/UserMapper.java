package com.spongebob.magic_conch_backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.spongebob.magic_conch_backend.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 只要继承 BaseMapper，增删改查全自动搞定！
}