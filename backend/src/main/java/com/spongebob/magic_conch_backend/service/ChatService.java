package com.spongebob.magic_conch_backend.service;

import com.spongebob.magic_conch_backend.entity.ChatSession;
import com.spongebob.magic_conch_backend.entity.ChatMessage;
import java.util.List;
import java.util.Map;

public interface ChatService {

    // 1. 生成回答 (注意这里加了 Long userId)
    Map<String, Object> callAiForOneReply(String prompt, Long sessionId, Long userId);

    // 2. 根据 userId 查询会话列表 (旧的无参 getSessionList 已经被我们彻底开除了！)
    List<ChatSession> getSessionListByUserId(Long userId);

    // 3. 获取历史记录
    List<ChatMessage> getHistoryBySessionId(Long sessionId);

    // 4. 删除会话
    void deleteSession(Long sessionId);
}