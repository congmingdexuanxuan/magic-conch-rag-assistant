from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
import requests
import uvicorn
import re
import os

# ==========================================
# 0. 唤醒真正的大脑 (这里以 DeepSeek 为例)
# 如果用的是其他的，改一下 base_url 和 api_key 即可
# ==========================================

# 找到与当前 Python 文件处于同一目录的 .env
env_file_path = (
    Path(__file__).resolve().parent / ".env"
)

# 把 .env 中的配置加载到当前 Python 进程
load_dotenv(env_file_path)
# 从 .env 读取大模型配置
llm_api_key = os.getenv("LLM_API_KEY")

llm_base_url = os.getenv(
    "LLM_BASE_URL",
    "https://api.siliconflow.cn/v1"
)

llm_model = os.getenv(
    "LLM_MODEL",
    "Pro/deepseek-ai/DeepSeek-V3.2"
)

# API Key 是必需配置
# 如果没有读取到，就在程序启动时明确报错
if not llm_api_key:
    raise RuntimeError(
        "没有读取到 LLM_API_KEY，"
        "请检查 magic_conch_agent/.env 文件。"
    )

# 使用从环境变量读取的配置创建大模型客户端
llm = ChatOpenAI(
    api_key=llm_api_key,
    base_url=llm_base_url,
    model=llm_model
)


# 从 .env 读取 RAGFlow 配置
ragflow_api_key = os.getenv(
    "RAGFLOW_API_KEY"
)

ragflow_url = os.getenv(
    "RAGFLOW_URL"
)

# RAGFlow 的 Key 和 URL 都是必需配置
if not ragflow_api_key:
    raise RuntimeError(
        "没有读取到 RAGFLOW_API_KEY，"
        "请检查 magic_conch_agent/.env 文件。"
    )

if not ragflow_url:
    raise RuntimeError(
        "没有读取到 RAGFLOW_URL，"
        "请检查 magic_conch_agent/.env 文件。"
    )

# 测试一下能否连通
# response = llm.invoke("你好，请用一句话证明你是 DeepSeek 大模型。")
# print(response.content)


# ==========================================
# 1. 这里可以理解为在langgraph当中的每个节点流转的数据 (State)
# 新增了 queries (搜索词) 和 retry_count (重试次数，防死循环)
# ==========================================

#  定义子问题结构
class SubEvidence(TypedDict):
    sub_question: str # 当前这份证据是为哪个子问题检索到的
    documents: str # 检索结果拼接成的完整文本
    chunks: List[str] # RAGFlow 返回的原始文本片段，用于后面去重


class AgentState(TypedDict):
    question: str   # 保存用户最初的问题
    queries: List[str]  # 保存用于检索知识库的关键词列表
    documents: str  # 保存从 RAGFlow 知识库检索回来的文档内容
    answer: str
    retry_count: int  # 核心：记录我们重试了几次
    ragflow_session_id: str # 用来存放 RAGFlow 的会话凭证
    # 用来判断该问题是简单还是复杂simple或者complex，Literal这样写得好处就是他规定了只能用这两个字符串
    question_type: Literal["simple", "complex"]
    sub_questions: List[str]  # 复杂问题拆出的 2～5 个子问题
    sub_evidences: List[SubEvidence] # 保存每个子问题及其独立检索结果，避免覆盖
    retrieved_chunks: List[str] # retrieve_node 单次检索返回的原始 chunk 文本列表
    merged_documents: str # 合并、去重后的证据，主要方便调试和观察


# ==========================================
# 2. 定义节点
# ==========================================

# 检索节点，确定要检索什么然后从ragflow拿到chunk再把资料放回agentstate
def retrieve_node(state: AgentState):
    # 拿出最新要想搜的词，会拿出这个list当中最后一个如果没有那么就会拿用户的问题，因为如果rewrite的话就会放到最后一个
    # 这里用中括号可以保证如果没有拿到数据一定是前端传数据过来的时候出问题了，如果出问题下面会拦截，这里一定要严格这样写
    search_query = state["queries"][-1] if state.get("queries") else state["question"]
    print(f"[检索工人] 正在前往 RAGFlow 查找真实资料：【{search_query}】...")

    # 看看此时公文包里到底有没有存着 session_id
    current_session = state.get("ragflow_session_id", "")
    print(f"[Debug] 当前公文包里的 session_id 是: '{current_session}'")

    # 1. 组装去 RAGFlow 的 URL，这一步已经放到上面的os那里去了

    # 2. 组装信封（带上你 Java 里的那个真实密钥）
    headers = {
        "Content-Type": "application/json",
        # Bearer 后面拼接从 .env 读取的 RAGFlow API Key
        "Authorization": f"Bearer {ragflow_api_key}"
    }
    #【核心新增：首次握手特判】
    if not current_session:
        print("[检索工人] 检测到新会话！正在悄悄向 RAGFlow 发送握手包骗取 ID...")
        try:
            # 随便发一句“你好”，主动触发它的开场白机制，这里是主动向RAGFLOW发一个POST请求
            handshake_payload = {"question": "你好", "stream": False}    # stream 表示：RAGFlow 返回答案时，是一次性全部返回，还是生成一点就返回一点。
            handshake_res = requests.post(ragflow_url, headers=headers, json=handshake_payload, timeout=30)
            # 把骗到的 ID 抓出来
            current_session = handshake_res.json().get("data", {}).get("session_id", "")
            print(f"[检索工人] 握手成功！骗到的专属 session_id: '{current_session}'")
        except Exception as e:
            print(f"[检索工人] 握手出现小意外: {e}，将尝试强行发送。")
    # 3. 组装问题
    payload = {
        "question": search_query,
        "stream": False  # 不要流式，等它一次性全给过来
    }
    if current_session:
        payload["session_id"] = current_session

    # 看看咱们发给 RAGFlow 的包裹里到底装了什么？
    print(f"[Debug] 即将发给 RAGFlow 的包裹: {payload}")
    try:
        # 发送真实的 POST 请求！
        response = requests.post(ragflow_url, headers=headers, json=payload, timeout=(5, 300))
        # response = requests.post(ragflow_url, headers=headers, json=payload ,timeout=30)
        response_data = response.json()

        print(f"[Debug] RAGFlow 原始返回：{response_data}")
        # 扒开 RAGFlow 返回的复杂 JSON 外衣，提取最核心的 answer（包含引用的文档）
        data = response_data.get("data", {})

        # 挖底层的 chunks, 这样把几个底层相关的chunks重新拼成文本然后再为给大模型做参考资料
        # 从 RAGFlow 返回结果中取出原始 chunks
        chunks = data.get("reference", {}).get("chunks", [])

        # 单独保存每个 chunk 的文本内容
        # 后面复杂问题合并资料时，会使用这个列表进行去重
        chunk_texts = []

        for chunk in chunks:
            # chunk.get("content") 可能是字符串，也可能是 None
            # 使用 or "" 可以把 None 转成空字符串，正常来说这里应该返回的已经是string但是万一返回其他类型为了防止报错这里写成str
            content = str(chunk.get("content") or "").strip()

            # 只保存不是空字符串的内容
            if content:
                chunk_texts.append(content)

        # documents 仍然是字符串
        # 这样现有的 grade_node 和 generate_node 不需要修改读取方式
        if chunk_texts:
            real_doc = "\n".join(chunk_texts)
        else:
            real_doc = ""

        # 如果没有找到真实资料，保留原来的防空包提示
        if not real_doc:
            real_doc = "RAGFlow 知识库中未检索到任何相关文字内容。"

        # 优先使用 RAGFlow 本次返回的 session_id
        # 如果本次没有返回，就继续使用原来的 current_session
        new_session_id = data.get("session_id") or current_session

        print(
            f"[检索工人] 成功拿回真实资料！"
            f"(记住的会话ID: {new_session_id})\n"
        )
        return {
            # 原来的字符串字段，继续提供给 grade 和 generate
            "documents": real_doc,
            # 新增的列表字段，复杂问题合并时用它去重
            "retrieved_chunks": chunk_texts,
            # 强制把最新的 session_id 更新到公文包里
            "ragflow_session_id": new_session_id
        }

    except Exception as e:
        print(f"[检索工人] 哎呀，连接 RAGFlow 失败了：{e}\n")
        return {
            "documents": "未能连接到知识库。",
            # 请求失败时没有可用的 chunk
            "retrieved_chunks": [],
            # 不要因为一次检索失败而丢掉已有的会话 ID
            "ragflow_session_id": current_session
        }


# ==========================================
# 依次检索复杂问题拆出的所有子问题
# ==========================================
def retrieve_subquestions_node(state: AgentState):
    # 取出拆解节点生成的所有子问题
    sub_questions = state.get("sub_questions", [])

    print(
        f"\n[多问题检索节点] 准备检索 "
        f"{len(sub_questions)} 个子问题。"
    )

    # 正常的简单问题不会进入这个节点。
    # 只有复杂问题拆解异常、手动调用错误或 State 异常时，
    # 才可能出现 sub_questions 为空的情况。
    # 后续 LangGraph 条件边会根据这个结果退回普通 retrieve。
    if not sub_questions:
        print(
            "[多问题检索节点] 没有可检索的子问题，"
            "退回简单问题流程。\n"
        )

        return {
            "question_type": "simple",
            "sub_evidences": []
        }

    # 保存所有子问题及其对应的检索结果
    sub_evidences = []

    # 第一个子问题使用当前 State 里的 RAGFlow session_id。
    # 如果是新会话，这里就是空字符串。
    current_session_id = state.get(
        "ragflow_session_id",
        ""
    )

    # 按照子问题原来的顺序，逐个执行检索，这样写就多能拿到编号
    for index, sub_question in enumerate(
        sub_questions,
        start=1
    ):
        print(
            f"\n[多问题检索节点] "
            f"开始检索第 {index}/{len(sub_questions)} 个子问题："
        )
        print(f"【{sub_question}】")

        # 为当前子问题创建一个临时 State
        #
        # **state 会复制原 State 中已有的内容，这个叫做字典解包；
        # 后面同名字段会覆盖复制进来的旧值，搞了个临时的节点。
        temporary_state = {
            **state,

            # 临时把 question 换成当前子问题，
            # 但不会修改真正 State 中的原始 question。
            "question": sub_question,

            # 清空 queries，确保 retrieve_node 使用当前子问题，
            # 而不是使用 rewrite_node 以前生成的检索词。
            "queries": [],

            # 清空当前临时检索结果，避免和上一次资料混淆。
            "documents": "",
            "retrieved_chunks": [],

            # 所有子问题依次使用当前的 RAGFlow session_id。
            "ragflow_session_id": current_session_id
        }

        try:
            # 直接复用现有的 retrieve_node。
            # result 只代表当前这个子问题的检索结果。
            result = retrieve_node(temporary_state)

            # 当前子问题拼接后的完整检索文本
            current_documents = str(
                result.get("documents") or ""
            )

            # 当前子问题检索到的原始 chunks
            current_chunks = (
                result.get("retrieved_chunks") or []
            )

            # 如果 retrieve_node 返回了新的 session_id，
            # 就使用新 ID；否则继续保留原来的 ID。
            current_session_id = (
                result.get("ragflow_session_id")
                or current_session_id
            )

            print(
                f"[多问题检索节点] 第 {index} 个子问题"
                f"检索完成，共取得 {len(current_chunks)} 个 chunk。"
            )

        except Exception as e:
            # 即使某一个子问题发生意外，
            # 也不要让后面的其他子问题全部停止检索。
            print(
                f"[多问题检索节点] 第 {index} 个子问题"
                f"检索失败：{e}"
            )

            current_documents = "当前子问题未能完成知识库检索。"
            current_chunks = []

        # 把当前子问题和它自己的检索结果绑定在一起保存。
        #
        # 不直接写全局 documents，
        # 因为下一次检索会覆盖上一次的 documents。
        sub_evidences.append({
            "sub_question": sub_question,
            "documents": current_documents,
            "chunks": current_chunks
        })

    print(
        f"\n[多问题检索节点] 所有子问题检索完成，"
        f"共保存 {len(sub_evidences)} 份检索结果。\n"
    )

    return {
        # 保存每个子问题和它对应的资料
        "sub_evidences": sub_evidences,

        # 保存最后确认过的 RAGFlow session_id
        "ragflow_session_id": current_session_id
    }

# ==========================================
# 合并并去重所有子问题的检索资料，这里有点细节没看懂
# ==========================================
def merge_evidence_node(state: AgentState):
    # 取出多问题检索节点保存的全部结果
    sub_evidences = state.get("sub_evidences", [])

    print(
        f"\n[证据合并节点] 准备合并 "
        f"{len(sub_evidences)} 份子问题资料。"
    )

    # 保存已经出现过的 chunk 特征
    # set 的特点是不会保存重复值，适合用于去重判断
    seen_chunk_keys = set()

    # 保存最终的资料分组
    evidence_sections = []

    # 用于日志统计
    original_chunk_count = 0
    unique_chunk_count = 0

    # 依次处理每一个子问题的资料，sub_evidences就是上面每个子问题对应的资料
    # 字典.get("要查找的key", "找不到时使用的默认值")
    for evidence in sub_evidences:
        sub_question = evidence.get(
            "sub_question",
            "未知子问题"
        )
        # 这里为了避免key存在但是里面是none，如果是none的话下面for那里会报错
        chunks = evidence.get("chunks", []) or []

        # 保存当前子问题去重后还剩下的 chunks
        unique_chunks_for_question = []

        for chunk in chunks:
            original_chunk_count += 1

            # 防止 chunk 是 None 或其他类型
            chunk_text = str(chunk or "").strip()

            # 空内容不作为有效资料
            if not chunk_text:
                continue

            # 生成专门用于比较的文本
            #
            # re.sub(r"\s+", "", chunk_text)
            # 会删除用于比较的文本中的空格和换行，
            # 避免同一段内容仅因换行不同而无法去重。
            chunk_key = re.sub(
                r"\s+",
                "",
                chunk_text
            ).lower()

            # 如果已经出现过相同内容，就跳过
            if chunk_key in seen_chunk_keys:
                continue

            # 第一次遇到这段内容，记录它
            seen_chunk_keys.add(chunk_key)

            # 保留原始文本，而不是保存删除空格后的 chunk_key
            unique_chunks_for_question.append(chunk_text)
            unique_chunk_count += 1

        # 当前子问题至少有一条有效资料时，
        # 才把它加入最终合并结果。
        if unique_chunks_for_question:
            section_text = (
                f"【子问题】{sub_question}\n"
                f"【检索资料】\n"
                + "\n\n".join(unique_chunks_for_question)
            )

            evidence_sections.append(section_text)

    # 所有子问题处理完成后，拼成一个完整字符串
    if evidence_sections:
        merged_documents = "\n\n".join(
            evidence_sections
        )
    else:
        # 如果所有子问题都没有检索到有效 chunks，
        # 给 grade_node 一个明确的失败说明。
        merged_documents = (
            "RAGFlow 知识库中未检索到足以回答"
            "该复杂问题的相关资料。"
        )

    print(
        f"[证据合并节点] 原始 chunk 数量："
        f"{original_chunk_count}"
    )

    print(
        f"[证据合并节点] 去重后 chunk 数量："
        f"{unique_chunk_count}"
    )

    print("[证据合并节点] 证据合并完成。\n")

    return {
        # 新字段：明确保存复杂问题的合并结果，
        # 方便以后查看和调试。
        "merged_documents": merged_documents,

        # 兼容现有 grade_node 和 generate_node。
        # 它们继续读取 documents，不需要大改。
        "documents": merged_documents
    }




# ==========================================
# 判断用户问题是简单问题还是复杂问题
# ==========================================
def classify_question_node(state: AgentState):
    # 原始问题始终保存在 question 中
    original_question = state["question"]

    print(
        f"\n[问题分类节点] 正在判断问题类型："
        f"【{original_question}】"
    )

    prompt = f"""
            你是一个问题结构分类器。
        
            你的任务不是回答问题，也不是判断问题的专业难度，
            更不是预测知识库一次能否检索到足够资料。
        
            你只需要判断：
        
            用户问题中是否包含多个可以分别检索、
            分别回答的相对独立的信息目标。
        
            【SIMPLE】
        
            问题只有一个核心信息目标，不需要拆成多个独立问题。
        
            即使问题专业、答案较长或者可能包含多个原因，
            只要用户最终只在询问一个核心目标，仍然判断为 SIMPLE。
        
            示例：
        
            什么是混流式水轮机？
            混流式水轮机为什么会发生振动？
            非定常空化条件下转轮叶片压力脉动机理是什么？
        
            【COMPLEX】
        
            问题包含两个或两个以上可以分别检索、
            分别回答的相对独立的信息目标。
        
            常见情况包括：
        
            1. 同时询问原因、危害、诊断和处理措施；
            2. 比较多个对象的多个不同方面；
            3. 一个问题中明确包含多个并列问题；
            4. 完整回答时需要分别处理多个主题或维度。
        
            示例：
        
            混流式水轮机振动的原因、危害和处理措施分别是什么？
            比较混流式和轴流式水轮机的适用水头、结构特点和运行性能。
            分析水轮机空化的形成机理，并说明其影响和防治方法。
        
            【用户问题】
        
            {original_question}
        
            只允许输出下面两个单词中的一个：
        
            SIMPLE
            COMPLEX
        
            不要输出解释、标点符号或其他内容。
            """

    try:
        # 调用现有的大模型进行判断
        response = llm.invoke(prompt)

        # 取出模型返回的文本并进行整理
        classification_result = response.content.strip().upper()

        print(
            f"[问题分类节点] 模型原始判断结果："
            f"【{classification_result}】"
        )

        if classification_result == "COMPLEX":
            question_type = "complex"

        elif classification_result == "SIMPLE":
            question_type = "simple"

        else:
            # 如果模型没有按照要求返回标准格式，
            # 为了不破坏原来的流程，默认按简单问题处理
            print(
                "[问题分类节点] 返回格式不正确，"
                "默认按照简单问题处理。"
            )
            question_type = "simple"

    except Exception as e:
        # 分类模型调用失败时，不让整个聊天接口直接失败
        # 默认走原来的简单问题流程
        print(
            f"[问题分类节点] 分类失败：{e}，"
            f"默认按照简单问题处理。"
        )
        question_type = "simple"

    print(
        f"[问题分类节点] 最终问题类型："
        f"【{question_type}】\n"
    )

    return {
        "question_type": question_type
    }

# ==========================================
# 将复杂问题拆成 2～5 个独立子问题
# ==========================================
def decompose_question_node(state: AgentState):
    # 永远从 question 中读取用户最初的原始问题
    original_question = state["question"]

    print(
        f"\n[问题拆解节点] 正在拆解复杂问题："
        f"【{original_question}】"
    )

    prompt = f"""
            你是一个问题拆解助手。
            
            请把下面的复杂问题拆成 2～5 个适合知识库检索的子问题。
            
            拆解要求：
            
            1. 每个子问题只关注一个主要主题或比较维度；
            2. 每个子问题必须能够独立理解；
            3. 不要使用“它”“这个”“上述”等指代不明确的词；
            4. 所有子问题合起来必须覆盖原始问题的全部要求；
            5. 不要回答问题，只负责拆解；
            6. 不要生成重复或含义高度相似的子问题；
            7. 对于比较类问题，优先按照比较维度进行拆解，
               并把需要比较的对象保留在同一个子问题中；
            8. 最终必须输出 2～5 个子问题；
            9. 如果自然拆解后超过 5 个，请合并相关的子问题，
               但不能直接省略原始问题中的任何要求；
            10. 每行只输出一个子问题；
            11. 不要添加序号、标题、解释或其他内容。
            
            【原始问题】
            
            {original_question}
            
            请直接输出拆解后的子问题，每行一个。
            """

    try:
        response = llm.invoke(prompt)

        # 模型返回的原始文本
        raw_result = response.content.strip()

        print(
            f"[问题拆解节点] 模型原始返回：\n"
            f"{raw_result}"
        )

        sub_questions = []

        # 按换行切开，让每一行成为一个候选子问题，因为上面prompt已经设置过了所以可以这样写
        for line in raw_result.splitlines():
            cleaned_question = line.strip()

            # 即使模型不听要求加了“1.”“2、”“（3）”等序号，
            # 也只删除真正位于行首的列表序号。
            #
            # 不使用 lstrip，是为了避免把“2020年……”中的年份误删。
            cleaned_question = re.sub(
                r"^\s*(?:\d+[.．、)）]|[（(]\d+[)）])\s*",
                "",
                cleaned_question
            )

            # 跳过空行
            if not cleaned_question:
                continue

            # 避免保存完全相同的子问题
            if cleaned_question not in sub_questions:
                sub_questions.append(cleaned_question)

        # 合法的拆解结果必须包含 2～5 个子问题
        # 不能直接使用 [:5] 截断，因为截断可能丢失原始问题中的要求
        if len(sub_questions) < 2 or len(sub_questions) > 5:
            print(
                f"[问题拆解节点] 得到了 "
                f"{len(sub_questions)} 个子问题，"
                f"不符合 2～5 个的要求，"
                f"退回简单问题流程。\n"
            )

            return {
                "question_type": "simple",
                "sub_questions": []
            }

        print("[问题拆解节点] 最终子问题：")

        for index, sub_question in enumerate(
            sub_questions,
            start=1
        ):
            print(f"  {index}. {sub_question}")

        print()

        return {
            "sub_questions": sub_questions
        }

    except Exception as e:
        # 拆解失败时退回原来的简单问题流程
        print(
            f"[问题拆解节点] 拆解失败：{e}，"
            f"退回简单问题流程。\n"
        )

        return {
            "question_type": "simple",
            "sub_questions": []
        }



# 用来判断下一步怎么走
def grade_node(state: AgentState):
    print("[质检工人] 正在呼叫 AI 裁判评估资料...")
    if state.get("retry_count", 0) >= 5:
        print("警告：已经重试了 5 次，查不到就算了！强制放行去生成答案！")
        return "generate"
    # 给 AI 裁判的指令，要求它只准回答 YES 或 NO
    prompt = f"""
    你是一个严格的水利工程质检员。
    【用户问题】：{state["question"]}
    【搜到的资料】：{state.get("documents", "")}

    请判断这份资料是否与用户问题【高度相关】？
    即使资料提供的是“功率”而用户问的是“效率”，只要属于同一技术领域且有参考价值，也请判定为 YES。
    如果资料里写着“未检索到”或完全无关，才判定为 NO。
    如果能，请只输出四个字母：YES
    如果不能，请只输出四个字母：NO
    警告：绝对不要输出任何标点符号和其他废话！
    """
    print(prompt)
    response = llm.invoke(prompt) #这里调用大模型进行判断
    result = response.content.strip().upper()  # 拿到结果，转大写去空格

    # 根据真实 AI 的回答来决定路线
    if "YES" in result:
        print(" AI 裁判判定：合格！直接去生成答案！")
        return "generate"
    else:
        print(f"AI 裁判判定：不合格！({result}) 打回重写！")
        return "rewrite"


# 重写收到的prompt
def rewrite_node(state: AgentState):
    print("[翻译工人] 资料没用，正在让 AI 重新思考检索词...")

    # 组装 Prompt，逼着大模型发挥它的专业词汇量
    prompt = f"""
    你是一个专业的水利工程检索专家。
    用户原本的问题是：【{state["question"]}】
    但是我们用原问题在数据库里搜不到对应的资料。

    请你根据原问题，提炼或改写出 2-3 个更专业的水利检索关键词，用空格隔开。
    例如：溢洪道 泄流量 计算
    警告：只输出关键词，绝对不要输出任何标点符号、前言后语或解释说明！
    """

    # 真实呼叫 AI ！
    response = llm.invoke(prompt) #这个不是ragflow里面的那个llm要做区分
    new_query = response.content.strip()  # 拿到 AI 绞尽脑汁想出的新词

    current_retries = state.get("retry_count", 0) + 1
    print(f"AI 灵光一闪，想到了新检索词：【{new_query}】。(这是第 {current_retries} 次重试)\n")

    # 把新词塞进公文包，重试次数加 1
    queries = state.get("queries", []) + [new_query]
    return {"queries": queries, "retry_count": current_retries}


def generate_node(state: AgentState):
    print("[生成工人] 正在呼叫真实的大模型为您解答...")

    # 1. 组装发给大模型的提示词 (Prompt)
    prompt = f"""
    你是一个专业的水利工程助理。请根据我提供的【参考资料】，回答【用户问题】。

    【参考资料】：{state.get("documents", "")}
    【用户问题】：{state["question"]}

    要求：语气专业，条理清晰，必须要用到参考资料里的内容。
    """

    # 2. 真实呼叫 AI ！(这一步需要联网，可能会等一两秒)
    response = llm.invoke(prompt) #这个不是ragflow里面的那个llm要做区分

    print("[生成工人] 大模型回答完毕！\n")

    # 3. 把大模型真正想出来的回答塞进公文包
    # response.content 就是大模型返回的文本内容
    return {"answer": response.content}


# ==========================================
# 根据 State 中的数据决定 LangGraph 下一步走向
# ==========================================

def route_after_classification(state: AgentState):
    """
    分类完成后的路线：
    simple  -> 原来的 retrieve
    complex -> decompose_question
    """
    if state.get("question_type") == "complex":
        return "complex"

    return "simple"


def route_after_decomposition(state: AgentState):
    """
    拆解完成后的路线：

    拆解成功，并且确实得到了子问题：
        -> retrieve_subquestions

    拆解失败或子问题为空：
        -> 退回原来的 retrieve
    """
    if (
        state.get("question_type") == "complex"
        and state.get("sub_questions")
    ):
        return "retrieve_subquestions"

    return "retrieve"


def route_after_subquestion_retrieval(state: AgentState):
    """
    多子问题检索完成后的路线：

    有保存下来的子问题检索结果：
        -> merge_evidence

    没有任何结果：
        -> 退回原来的 retrieve
    """
    if state.get("sub_evidences"):
        return "merge_evidence"

    return "retrieve"




# ==========================================
# 3. 缝合复杂的图结构 (有循环的 Graph)
# ==========================================
workflow = StateGraph(AgentState)

# ==========================================
# 1. 注册所有节点
# ==========================================

# 新增的复杂问题处理节点
workflow.add_node(
    "classify_question",
    classify_question_node
)

workflow.add_node(
    "decompose_question",
    decompose_question_node
)

workflow.add_node(
    "retrieve_subquestions",
    retrieve_subquestions_node
)

workflow.add_node(
    "merge_evidence",
    merge_evidence_node
)

# 原来已有的节点
workflow.add_node(
    "retrieve",
    retrieve_node
)

workflow.add_node(
    "rewrite",
    rewrite_node
)

workflow.add_node(
    "generate",
    generate_node
)


# ==========================================
# 2. 从问题分类开始
# ==========================================

workflow.add_edge(
    START,
    "classify_question"
)


# ==========================================
# 3. 分类完成：简单问题或复杂问题
# ==========================================

workflow.add_conditional_edges(
    "classify_question",
    route_after_classification,
    {
        # 简单问题直接进入原来的检索流程
        "simple": "retrieve",

        # 复杂问题先进行拆解
        "complex": "decompose_question"
    }
)


# ==========================================
# 4. 拆解完成：多问题检索或退回原流程
# ==========================================

workflow.add_conditional_edges(
    "decompose_question",
    route_after_decomposition,
    {
        # 拆解成功
        "retrieve_subquestions": "retrieve_subquestions",

        # 拆解失败时退回原来的单问题检索
        "retrieve": "retrieve"
    }
)


# ==========================================
# 5. 多子问题检索完成：合并资料或退回
# ==========================================

workflow.add_conditional_edges(
    "retrieve_subquestions",
    route_after_subquestion_retrieval,
    {
        # 已经拿到各个子问题的资料
        "merge_evidence": "merge_evidence",

        # 没有子问题资料，退回原来的检索
        "retrieve": "retrieve"
    }
)


# ==========================================
# 6. 普通检索完成后，使用原来的 grade
# ==========================================

workflow.add_conditional_edges(
    "retrieve",
    grade_node,
    {
        "rewrite": "rewrite",
        "generate": "generate"
    }
)


# ==========================================
# 7. 复杂问题资料合并后，也进入现有 grade
# ==========================================

workflow.add_conditional_edges(
    "merge_evidence",
    grade_node,
    {
        "rewrite": "rewrite",
        "generate": "generate"
    }
)


# ==========================================
# 8. grade 不通过：沿用原来的重写和重新检索
# ==========================================

workflow.add_edge(
    "rewrite",
    "retrieve"
)


# ==========================================
# 9. 生成答案后结束
# ==========================================

workflow.add_edge(
    "generate",
    END
)


# 编译完整工作流
app = workflow.compile()

# ==========================================
# 4. 运行测试
# ==========================================
# if __name__ == "__main__":
#     print(" === 带有反思循环的测试开始 === \n")
#     initial_state = {
#         "question": "励磁效率公式？",
#         "retry_count": 0,
#         "queries": []
#     }
#
#     final_state = app.invoke(initial_state)
#
#     print("\n === 最终公文包状态 === ")
#     print(f"最终重试次数: {final_state['retry_count']}")
#     print(f"用过的搜索词: {final_state['queries']}")


# ==========================================
# 【终极融合】：FastAPI 接口层
# ==========================================

# 1. 定义前端/Java 传过来的数据长什么样（数据模型）
class ChatRequest(BaseModel):
    question: str
    session_id: str = ""  # 如果前端没传，默认是空（新会话）
    is_mock: bool = False  # Mock 开关，默认是 False（走真实流程）

# 2. 实例化 FastAPI 应用程序
api_app = FastAPI(title="大聪明智慧问答 - 企业级 RAG 智能体")


# 3. 开放一个 POST 接口，暴露给外界调用
@api_app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"\n[接口层] 收到外部请求！问题：【{request.question}】 会话ID：【{request.session_id}】 Mock模式：【{request.is_mock}】")
    # Mock 断路器

    # 如果请求要求走 Mock 模式，直接在这里拦截并返回假数据
    if request.is_mock:
        print("[接口层]触发 Mock 模式！跳过 LangGraph，直接返回测试数据。")
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "answer": f"【Mock 测试返回】这是一条假数据。我已经收到了你的问题：'{request.question}'。当前没有消耗任何 Token，也没有调用大模型。",
                "session_id": request.session_id if request.session_id else "mock_test_session_999"
            }
        }

    # 如果 is_mock 是 False，继续走下方的真实 LangGraph 流程
    print("[接口层] 走真实模式，准备唤醒 LangGraph 流水线...")
    # 组装丢给 LangGraph 的初始公文包
    initial_state = {
        # 用户最初的问题
        "question": request.question,

        # 原有流程使用的字段
        "queries": [],
        "documents": "",
        "answer": "",
        "retry_count": 0,
        "ragflow_session_id": request.session_id or "",

        # 复杂问题流程使用的字段
        "question_type": "simple",
        "sub_questions": [],
        "sub_evidences": [],
        "retrieved_chunks": [],
        "merged_documents": ""
    }

    #启动你的 LangGraph 流水线！（假设你上面的图纸编译后叫 app,也就是上面的工作流）
    try:
        final_state = app.invoke(initial_state)

        print("[接口层] LangGraph 执行完毕，准备将数据打包返回给前端！")

        # 把最终答案和可能更新过的 session_id 包装成 JSON 返回
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "answer": final_state["answer"],
                "session_id": final_state.get("ragflow_session_id", "")
            }
        }
    except Exception as e:
        print(f"[接口层] 发生大崩盘：{e}")
        return {
            "code": 500,
            "msg": f"AI 大脑短路了: {str(e)}",
            "data": None
        }

# 4. 启动服务器的指令
if __name__ == "__main__":
    print("FastAPI 服务器正在启动... 监听端口 8000")
    # 注意：这里的 api_app 就是上面实例化的 FastAPI 对象
    uvicorn.run(api_app, host="0.0.0.0", port=8000)