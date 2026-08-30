package com.spongebob.magic_conch_backend.common.vo;


import com.spongebob.magic_conch_backend.common.enums.ResultCode;

import java.io.Serial;
import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

/**
 * api接口数据返回封装
 *
 */
public class Result implements Serializable {
//Result 类的核心作用是作为后端向前端返回数据的统一标准封装体。它的本质是前后端之间约定的一套通信协议数据结构。
    @Serial
    private static final long serialVersionUID = -4762928619495260423L;

    private Integer code;// 用来告诉前端请求是否成功

    private String msg;// 一段文字。通常用来存放“成功”、“系统异常”、“密码错误”这样的提示语。

    private Object data;// 实际的业务数据。比如你从数据库查出来的历史记录，或者调用 AI 得到的回复，都会塞到这个变量里。

    public Result() {
    }

    public Result(Integer code, String msg) {
        this.code = code;
        this.msg = msg;
    }

    public static Result success() {
        Result result = new Result();
        result.setResultCode(ResultCode.SUCCESS);
        result.setMsg("成功");
        return result;
    }

    public static Result success(Object data) {
        Result result = success();
        result.setData(data);
        return result;
    }

    public static Result success(Object data, String msg) {
        Result result = success();
        result.setData(data);
        result.setMsg(msg);
        return result;
    }

    public static Result error() {
        Result result = new Result();
        result.setResultCode(ResultCode.ERROR);
        result.setMsg("系统异常");
        return result;
    }

    public static Result error(String msg) {
        Result result = new Result();
        result.setResultCode(ResultCode.ERROR);
        result.setMsg(msg);
        return result;
    }

    public static Result error(ResultCode resultCode) {
        Result result = new Result();
        result.setResultCode(resultCode);
        result.setMsg("系统异常");
        return result;
    }

    public static Result error(ResultCode resultCode, String msg) {
        Result result = new Result();
        result.setResultCode(resultCode);
        result.setMsg(msg);
        return result;
    }

    public static Result error(ResultCode resultCode, Object data) {
        Result result = error(resultCode);
        result.setData(data);
        return result;
    }

    public static Result error(ResultCode resultCode, Object data, String msg) {
        Result result = error(resultCode);
        result.setData(data);
        result.setMsg(msg);
        return result;
    }

    public void setResultCode(ResultCode code) {
        this.code = code.code();
        this.msg = code.message();
    }


    public Map<String, Object> simple() {
        Map<String, Object> simple = new HashMap<String, Object>();
        this.data = simple;

        return simple;
    }

    public Integer getCode() {
        return code;
    }

    public void setCode(Integer code) {
        this.code = code;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }

    public Object getData() {
        return data;
    }

    public void setData(Object data) {
        this.data = data;
    }


}