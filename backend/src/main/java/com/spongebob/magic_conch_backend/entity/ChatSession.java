package com.spongebob.magic_conch_backend.entity;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.util.Date;

@Data // 用Lombok，自动帮你写 get/set 方法！
@TableName("chat_session") // 告诉 Java 这个类对应数据库的哪张表
public class ChatSession {

    @TableId(type = IdType.AUTO) // 告诉 Java 这是主键，而且是自增的
    private Long id;

    private String title;

    private String ragflowSessionId; // 驼峰命名法，自动对应数据库的 ragflow_session_id

    private Date createTime;

    private Long userId; // 【新增】能够让每个用户的对话分隔开
}