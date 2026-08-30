from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ==========================================
# 1. 定义公文包 (State)
# 这就是流水线上那个传来传去的包，规定了里面能装什么
# ==========================================
class AgentState(TypedDict):
    question: str  # 用户的提问
    documents: str  # 搜到的资料
    answer: str  # 最终的回答


# ==========================================
# 2. 定义节点工人 (Nodes)
# 每个函数就是一个只干一件事的工人。
# 规则：工人从 state 里拿东西，干完活后 return 一个字典，字典里的东西会自动更新到包里
# ==========================================
def retrieve_node(state: AgentState):
    print(" [检索工人] 收到问题：", state["question"])
    print(" [检索工人] 正在去知识库检索...")

    # 这里我们先不接 RAGFlow，假装搜到了结果
    fake_doc = "《水利规范》规定：大坝下泄流量公式为 Q = v * A"
    print(" [检索工人] 检索完成！把资料塞进包里。\n")

    # 返回的内容会自动覆盖 State 里的 documents
    return {"documents": fake_doc}


def generate_node(state: AgentState):
    print(" [生成工人] 拿到了前面的资料：", state.get("documents"))
    print(" [生成工人] 正在根据资料写回答...")

    # 这里先不接大模型，假装大模型写好了回答
    fake_answer = f"大聪明为您解答：根据您问的【{state['question']}】，结合资料，答案是 Q=v*A。"
    print(" [生成工人] 写完了！把答案塞进包里。\n")

    return {"answer": fake_answer}


# ==========================================
# 3. 缝合流水线 (Graph)
# 把工人们安排到生产线上，画出箭头指示方向
# ==========================================
workflow = StateGraph(AgentState)

# 注册工人
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

# 画箭头（这里是最简单的直线，还没加判断）
workflow.add_edge(START, "retrieve")  # 开始 -> 去检索
workflow.add_edge("retrieve", "generate")  # 检索完 -> 去生成
workflow.add_edge("generate", END)  # 生成完 -> 结束

# 编译成可运行的程序
app = workflow.compile()

# ==========================================
# 4. 试运行测试
# ==========================================
if __name__ == "__main__":
    print(" === 测试开始 === \n")

    # 模拟从 Java 传过来的初始公文包，里面只有问题
    initial_state = {"question": "泄洪流量怎么算？"}

    # 启动流水线 (invoke)
    final_state = app.invoke(initial_state)

    print(" === 最终公文包的状态 === ")
    print(final_state)