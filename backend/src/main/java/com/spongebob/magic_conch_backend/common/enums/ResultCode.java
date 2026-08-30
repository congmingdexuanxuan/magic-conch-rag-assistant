package com.spongebob.magic_conch_backend.common.enums;

/**
 * api接口返回 code和message
 *
 */
public enum ResultCode {

    /* 成功 */
    SUCCESS(100, "成功"),
    /* 参数无效 */
    PARAM_INVALID(101, "参数无效"),
    /* 业务异常 */
    ERROR(999, "业务异常");

    private Integer code;

    private String message;

    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }

    public Integer code() {
        return this.code;
    }

    public String message() {
        return this.message;
    }

    public static String getMessage(String name) {
        for (ResultCode item : ResultCode.values()) {
            if (item.name().equals(name)) {
                return item.message;
            }
        }
        return name;
    }

    public static Integer getCode(String name) {
        for (ResultCode item : ResultCode.values()) {
            if (item.name().equals(name)) {
                return item.code;
            }
        }
        return null;
    }

    @Override
    public String toString() {
        return this.name();
    }

}
