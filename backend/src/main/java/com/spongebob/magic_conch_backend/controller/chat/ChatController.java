package com.spongebob.magic_conch_backend.controller.chat;

import com.spongebob.magic_conch_backend.common.enums.ResultCode;
import com.spongebob.magic_conch_backend.common.vo.Result;
import com.spongebob.magic_conch_backend.service.ChatService;

import io.micrometer.common.util.StringUtils;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
//这个类是一个 REST API 控制器，里面的方法可以接收浏览器或前端发来的 HTTP 请求，并将返回值转换为 JSON。
@RequestMapping(value = "/chat")
@CrossOrigin
public class ChatController {

    @Autowired
    private ChatService chatService;

    // 【修改】：增加了一个 sessionId 参数，设为 false 表示可传可不传
    @RequestMapping("/generate")
    @ResponseBody
    //@RequestParam 的主要作用是：将 HTTP 请求中的参数（通常是 URL 中的查询参数，或者表单提交的数据）
    //提取出来，并自动赋值给 Controller 方法中的具体参数。
    public Result generate(@RequestParam String prompt,
                           @RequestParam(required = false) Long sessionId,
                           @RequestParam Long userId) {
        Result result = Result.success();// 返回一个请求成功的初始数据对象
        if(StringUtils.isBlank(prompt)) {
            return Result.error(ResultCode.PARAM_INVALID,"prompt不能为空");
        }
        try {
        // 调用服务，把 userId 传进去
            Map<String, Object> resMap = chatService.callAiForOneReply(prompt, sessionId, userId);
            result.setData(resMap);
        } catch (Exception e) {
            e.printStackTrace();
            result = Result.error();
        }
        return result;
    }
    // 【新加接口 1】：获取侧边栏会话列表
    @GetMapping("/sessions")
    public Result getSessionList(@RequestParam Long userId) { // 【新增参数】
        try {
            // 这里去 Service 里根据 userId 过滤
            return Result.success(chatService.getSessionListByUserId(userId));
        } catch (Exception e) {
            return Result.error();
        }
    }

    // 【新加接口 2】：获取某个会话的聊天历史
    @GetMapping("/history")
    public Result getHistory(@RequestParam Long sessionId) {
        //spring通过@RequestParam这个注释来分离url的参数
        try {
            return Result.success(chatService.getHistoryBySessionId(sessionId));
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error(); // <--- 这里也一样
        }
    }
    // 【新加接口 3】：删除历史对话
    @GetMapping("/deleteSession")
    public Result deleteSession(@RequestParam Long sessionId) {
        try {
            chatService.deleteSession(sessionId);
            return Result.success("删除成功");
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error();
        }
    }
}