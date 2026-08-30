# Magic Conch RAG Assistant

一个面向专业知识问答场景的全栈 RAG 聊天项目。前端使用 Vue，业务后端使用 Spring Boot，AI 服务使用 FastAPI 与 LangGraph，并通过 RAGFlow 检索知识库。

## 系统架构

```text
Vue frontend
    ↓ HTTP
Spring Boot backend
    ├── MySQL：用户、聊天会话与消息记录
    └── FastAPI /api/chat
            ↓
        LangGraph agent
            ↓
        RAGFlow knowledge base
```

## 核心功能

- 用户登录、聊天会话与历史消息管理
- Spring Boot 转发 AI 请求，并维护本地会话 ID 与 RAGFlow 会话 ID 的映射
- FastAPI 提供统一聊天接口和 Mock 模式
- LangGraph 编排 `retrieve → grade → rewrite → generate` 流程
- 自动区分简单问题与复杂问题
- 将复杂问题拆解为 2～5 个可检索的子问题
- 分别检索并保存每个子问题的 evidence，合并、去重后再评分与生成
- 限制重试次数，避免检索改写流程无限循环

## 目录结构

```text
.
├── frontend/   # Vue 3 + Vite + Element Plus
├── backend/    # Spring Boot 3 + MyBatis-Plus + MySQL
└── agent/      # FastAPI + LangGraph + RAGFlow
```

## 本地运行

### 1. 准备依赖

- Node.js 与 npm
- Java 17
- Python 3.11+
- MySQL
- 已启动并配置知识库的 RAGFlow

### 2. 配置后端

在 `backend` 目录中复制示例配置：

```powershell
Copy-Item .env.example .env
```

填写本地 MySQL 连接信息，然后启动：

```powershell
.\mvnw.cmd spring-boot:run
```

后端默认监听 `http://localhost:8080`。

### 3. 配置 Agent

在 `agent` 目录中创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

在 `.env` 中填写大模型与 RAGFlow 配置，然后启动：

```powershell
python agent_loop_test.py
```

Agent 默认监听 `http://localhost:8000`，接口文档位于 `http://localhost:8000/docs`。

### 4. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

## 环境变量

真实 `.env` 已被 Git 忽略，仓库只提供安全的示例文件：

- `backend/.env.example`
- `agent/.env.example`

请勿把数据库密码、LLM API Key 或 RAGFlow API Key 写入源码或提交到 Git。

## 当前状态

复杂问题拆解功能已完成代码接入与基础节点测试。完整的真实链路仍需在 MySQL、RAGFlow、Agent、Spring Boot 和前端全部启动后进行端到端验证。
