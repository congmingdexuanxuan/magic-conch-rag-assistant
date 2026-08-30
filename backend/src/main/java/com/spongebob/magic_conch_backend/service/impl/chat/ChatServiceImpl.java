package com.spongebob.magic_conch_backend.service.impl.chat;

import com.spongebob.magic_conch_backend.config.AiServiceConfig;
import com.spongebob.magic_conch_backend.entity.ChatMessage;
import com.spongebob.magic_conch_backend.entity.ChatSession;
import com.spongebob.magic_conch_backend.mapper.ChatMessageMapper;
import com.spongebob.magic_conch_backend.mapper.ChatSessionMapper;
import com.spongebob.magic_conch_backend.service.ChatService;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
// 这个注解告诉 Spring 框架：“这是一个处理核心业务逻辑的类，请把它实例化并放入内存中管理”。
// 正是因为有了它，你在 Controller 里才能使用 @Autowired 把这个类注入进去。
// 当 Spring 容器启动时，扫描到类上带有 @Service，它会在内存中主动实例化这个类（相当于底层替你执行了
// new 操作），并将创建好的对象实例（Bean）存入 Spring 的单例池中，只能作用于类（Class）级别。
public class ChatServiceImpl implements ChatService {

    @Autowired
    // 动作：当 Spring 实例化其他类（如 Controller）时，如果发现其内部有标记了
    // @Autowired 的字段，Spring 会去单例池中查找是否已经存在匹配类型的 Bean。如果找到了，
    // 就把该 Bean 的内存地址（引用）赋值给这个字段。
    // 作用位置：通常作用于字段（Field）、构造方法或Setter 方法级
    private RestTemplate restTemplate; //构造一个HTTP POST请求
    // RestTemplate 是 Spring 提供的一个 HTTP 客户端工具，用于让 Java 后端请求另一个 HTTP 服务。
    // 它不仅能发送 POST，也能发送 GET、PUT、DELETE 等请求。
    @Autowired
    private AiServiceConfig aiServiceConfig;

    @Autowired
    private ChatSessionMapper chatSessionMapper;
    @Autowired
    private ChatMessageMapper chatMessageMapper;


//    原本的只通过ragflow的代码
//    @SuppressWarnings("unchecked")
//    @Override
//    public Map<String, Object> callAiForOneReply(String prompt, Long sessionId, Long userId) {
//
//        // 【修复点 1】：提前准备好最后要返回给前端的包裹 (resultMap)
//        Map<String, Object> resultMap = new HashMap<>();
//
//        // 【修复点 2】：提前准备好 currentSession 变量
//        ChatSession currentSession;
//
//        if (sessionId == null) {
//            ChatSession newSession = new ChatSession();
//            newSession.setTitle(prompt.length() > 10 ? prompt.substring(0, 10) + "..." : prompt);
//            newSession.setUserId(userId);
//            newSession.setCreateTime(new java.util.Date());
//            chatSessionMapper.insert(newSession);
//
//            // 如果是新建的，那么当前会话就是刚刚建好的这个
//            currentSession = newSession;
//        } else {
//            // 【修复点 3】：把错写的 dbSessionId 改成了正确的 sessionId
//            currentSession = chatSessionMapper.selectById(sessionId);
//        }
//
//        // ================= 2. 保存【用户】的提问到数据库 =================
//        ChatMessage userMsg = new ChatMessage();
//        userMsg.setSessionId(currentSession.getId());
//        userMsg.setRole("user");
//        userMsg.setContent(prompt);
//        userMsg.setCreateTime(new Date());
//        chatMessageMapper.insert(userMsg);
//
//        // ================= 3. 准备向 RAGFlow 发送请求 =================
//        // 这里主要实现了后端如何找到服务器上的RagFlow
//        String url = String.format("%s/api/v1/chats/%s/completions", aiServiceConfig.getBaseUrl(), CONVERSATION_ID);
//        HttpHeaders headers = new HttpHeaders();
//        headers.setContentType(MediaType.APPLICATION_JSON);
//        headers.set("Authorization", "Bearer " + RAGFLOW_API_KEY);
//
//        Map<String, Object> requestBody = new HashMap<>();
//        requestBody.put("question", prompt);
//        requestBody.put("stream", false);
//
//        if (currentSession.getRagflowSessionId() != null && !currentSession.getRagflowSessionId().isEmpty()) {
//            requestBody.put("session_id", currentSession.getRagflowSessionId());
//        }
//
//        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
//        String finalAnswer = "未能获取有效回复";
//
//        try {
//            // ================= 4. 接收 RAGFlow 返回 =================
//            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
//            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
//                Map<String, Object> body = response.getBody();
//                Map<String, Object> data = (Map<String, Object>) body.get("data");
//
//                if (data != null) {
//                    if (data.containsKey("session_id")) {
//                        String ragId = data.get("session_id").toString();
//                        if (currentSession.getRagflowSessionId() == null) {
//                            currentSession.setRagflowSessionId(ragId);
//                            chatSessionMapper.updateById(currentSession);
//                        }
//                    }
//                    if (data.containsKey("answer")) {
//                        finalAnswer = data.get("answer").toString();
//                    }
//                }
//            }
//        } catch (Exception e) {
//            e.printStackTrace();
//            finalAnswer = "连接 RAGFlow 出错：" + e.getMessage();
//        }
//
//        // ================= 5. 保存【大聪明】的回答到数据库 =================
//        ChatMessage aiMsg = new ChatMessage();
//        aiMsg.setSessionId(currentSession.getId());
//        aiMsg.setRole("assistant");
//        aiMsg.setContent(finalAnswer);
//        aiMsg.setCreateTime(new Date());
//        chatMessageMapper.insert(aiMsg);
//
//        // ================= 6. 返回结果给前端 =================
//        resultMap.put("answer", finalAnswer);
//        resultMap.put("sessionId", currentSession.getId());
//        return resultMap;
//
//    }

    // ================= 查询与删除方法 =================
    @SuppressWarnings("unchecked")
    @Override
    public Map<String, Object> callAiForOneReply(String prompt, Long sessionId, Long userId) {

        Map<String, Object> resultMap = new HashMap<>();
        ChatSession currentSession;// 管理当前session下的每一个message

        if (sessionId == null) {
            // 前端没有传 sessionId，说明用户是在发起一段新聊天。
            ChatSession newSession = new ChatSession();
            newSession.setTitle(prompt.length() > 10 ? prompt.substring(0, 10) + "..." : prompt);
            newSession.setUserId(userId);
            newSession.setCreateTime(new java.util.Date());
            chatSessionMapper.insert(newSession);
            currentSession = newSession;
        } else {
            // 不是新聊天的情况
            currentSession = chatSessionMapper.selectById(sessionId);
        }

        // ================= 2. 保存【用户】的提问到数据库 =================
        ChatMessage userMsg = new ChatMessage();
        userMsg.setSessionId(currentSession.getId());
        userMsg.setRole("user");
        userMsg.setContent(prompt);
        userMsg.setCreateTime(new Date());
        chatMessageMapper.insert(userMsg);

        // ================= 3. 准备向 Python 发送请求 (核心修改区) =================

        // 【修改点 1】：把地址直接指向你跑着 LangGraph 的 Python 本地端口
        String url = "http://127.0.0.1:8000/api/chat";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        // 【修改点 2】：删掉了 RAGFlow 的 API Key。因为这事现在归 Python 管了，Java 不用操心！

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("question", prompt);
        // 【修改点 3】：不再需要 stream: false 参数了

        // 【修改点 4】：传递 session_id 给 Python，如果没有就传空字符串
        if (currentSession.getRagflowSessionId() != null && !currentSession.getRagflowSessionId().isEmpty()) {
            requestBody.put("session_id", currentSession.getRagflowSessionId());
        } else {
            requestBody.put("session_id", "");
        }

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
        String finalAnswer = "未能获取有效回复";

        try {
            // ================= 4. 接收 Python 返回 (解析代码几乎不用改！) =================
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                Map<String, Object> body = response.getBody();
                Map<String, Object> data = (Map<String, Object>) body.get("data");

                if (data != null) {
                    if (data.containsKey("session_id")) {
                        String ragId = data.get("session_id").toString();
                        if (currentSession.getRagflowSessionId() == null || currentSession.getRagflowSessionId().isEmpty()) {
                            currentSession.setRagflowSessionId(ragId);
                            chatSessionMapper.updateById(currentSession);
                        }
                    }
                    if (data.containsKey("answer")) {
                        finalAnswer = data.get("answer").toString();
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            finalAnswer = "连接 Python 智能体出错：" + e.getMessage();
        }

        // ================= 5. 保存【大聪明】的回答到数据库 =================
        ChatMessage aiMsg = new ChatMessage();
        aiMsg.setSessionId(currentSession.getId());
        aiMsg.setRole("assistant");
        aiMsg.setContent(finalAnswer);
        aiMsg.setCreateTime(new Date());
        chatMessageMapper.insert(aiMsg);

        // ================= 6. 返回结果给前端 =================
        resultMap.put("answer", finalAnswer);
        resultMap.put("sessionId", currentSession.getId());
        return resultMap;
    }

    @Override
    public List<ChatSession> getSessionListByUserId(Long userId) {
        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<ChatSession> queryWrapper = new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        queryWrapper.orderByDesc("create_time");
        return chatSessionMapper.selectList(queryWrapper);
    }

    @Override
    public List<ChatMessage> getHistoryBySessionId(Long sessionId) {
        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<ChatMessage> queryWrapper = new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        queryWrapper.eq("session_id", sessionId);
        queryWrapper.orderByAsc("create_time");
        return chatMessageMapper.selectList(queryWrapper);
    }

    @Override
    public void deleteSession(Long sessionId) {
        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<ChatMessage> queryWrapper = new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        queryWrapper.eq("session_id", sessionId);
        chatMessageMapper.delete(queryWrapper);

        chatSessionMapper.deleteById(sessionId);
    }
}