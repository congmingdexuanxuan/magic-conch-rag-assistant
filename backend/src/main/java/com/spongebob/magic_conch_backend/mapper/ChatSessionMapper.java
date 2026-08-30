package com.spongebob.magic_conch_backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.spongebob.magic_conch_backend.entity.ChatSession;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatSessionMapper extends BaseMapper<ChatSession> {
    // 空着就行！BaseMapper 里面已经帮你写好了 insert, update, selectById 等所有方法！
}