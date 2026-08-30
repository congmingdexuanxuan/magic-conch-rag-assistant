package com.spongebob.magic_conch_backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.spongebob.magic_conch_backend.entity.ChatMessage;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatMessageMapper extends BaseMapper<ChatMessage> {
}