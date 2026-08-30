package com.spongebob.magic_conch_backend.common.vo;

import java.io.Serializable;

public class PageParam implements Serializable {
    private static final long serialVersionUID = 1L;
    
    private Integer pageNum = 1;
    private Integer pageSize = 10;
    private String orderBy;

    public Integer getPageNum() {
        return pageNum;
    }

    public void setPageNum(Integer pageNum) {
        this.pageNum = pageNum;
    }

    public Integer getPageSize() {
        return pageSize;
    }

    public void setPageSize(Integer pageSize) {
        this.pageSize = pageSize;
    }

    public String getOrderBy() {
        return orderBy;
    }

    public void setOrderBy(String orderBy) {
        this.orderBy = orderBy;
    }
} 