# Question Decomposition RAG Evaluation

## 1. 实验目的

本实验用于比较普通 Single-query RAG 和 Question Decomposition RAG
在水利领域知识库问答中的实际效果。

本实验重点观察：

1. Question Decomposition 是否能找到更完整的证据；
2. Question Decomposition 是否能提高最终答案质量；
3. Question Decomposition 对哪些问题有效；
4. Question Decomposition 会在哪些情况下产生错误或噪声。

## 2. Research Question

在水利领域知识库的复杂问答中，
Question Decomposition 相比 Single-query RAG，
能否提高证据覆盖率和最终答案质量？

它在哪些类型的问题上有效，
在哪些问题上反而会降低效果？

## 3. 对比方法

### A. Single-query RAG

原始问题 → retrieve_node → generate_node

### B. Question Decomposition RAG

原始问题
→ decompose_question_node
→ retrieve_subquestions_node
→ merge_evidence_node
→ generate_node

## 4. 第一版暂不包含

为了只观察 Question Decomposition 带来的变化，
第一版实验暂时不使用：

- classify_question_node
- grade_node
- rewrite_node
- 语义重试

这些节点不会从正式 Agent 中删除，
只是在独立的 evaluation 实验中暂时不调用。

## 5. 实验假设

### H1：组合问题

对于包含多个相对独立信息目标的组合问题，
Question Decomposition 能够提高证据覆盖率和答案完整性。

### H2：简单事实问题

对于只包含一个核心信息目标的简单事实问题，
Question Decomposition 不会带来明显提升，
并可能因为过度拆解而引入无关信息。

### H3：多证据问题

对于需要结合多个知识点才能完整回答的问题，
Question Decomposition 更容易检索到所需的多份证据。

### H4：系统成本

Question Decomposition 会增加子问题生成、知识库检索次数和响应时间，
因此效果提升需要与额外成本一起评价。
