package com.spongebob.magic_conch_backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.util.Date;

@Data
@TableName("user") // 对应数据库里的 user 表
public class User {
    @TableId(type = IdType.AUTO)
    private Long id;          // 用户唯一ID
    private String username;  // 账号
    private String password;  // 密码 (新手期咱们先存明文，以后再教你加密)
    private Date createTime;  // 注册时间
}