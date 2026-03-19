# RAG Research Assistant

一个基于 Open Deep Research 的二次开发项目。在原有深度研究流程上，补齐了本地知识检索（RAG）、会话/长期记忆、可追溯证据输出和评测回归能力，适合做可持续迭代的研究助手。

## What This Version Adds

- 本地知识库检索：支持 md、txt、pdf、docx 入库到 Chroma
- 会话记忆：同线程自动继承偏好（例如中文、简洁、不要表格）
- 长期记忆：默认 explicit_confirmation，明确确认后才写入
- 三通道证据：web + local + memory，输出可追溯引用
- 运行时控制：支持 user_id、memory_mode、rag_scope
- 评测扩展：新增个性化、记忆有效性、来源多样性指标和回归矩阵

## 5-Minute Demo (For Interviewers)

1. 启动服务

```bash
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
```

2. 在 Studio 发送：请用中文简洁回答，不要表格，分析 2026 年 AI Agent 落地难点。
3. 在同一线程继续追问，确认风格自动延续。
4. 若开启长期记忆，发送“确认记忆”，新线程再提问，确认偏好仍生效。
5. 提问一个本地资料问题，确认回答里有本地来源引用。

预期结果：个性化可复现、本地检索可命中、关键结论可追溯。

## 你可以用它做什么

- 同时利用网络信息和本地资料完成研究与报告生成
- 在同一会话中记住表达偏好
- 在明确确认后写入长期偏好并跨会话复用
- 对关键结论给出可追踪来源，便于复核
- 用验收与评测脚本快速检查改造功能是否稳定

## 30 秒理解工作流

1. 用户提问并给出偏好（可选）
2. Agent 判断是否需要澄清
3. supervisor 拆解研究任务
4. researcher 并行调用工具（Web Search / Local RAG / Memory）
5. 汇总证据并生成最终报告
6. API 结果附带来源与过程信息

## 快速开始（普通用户路径）

### 1) 环境准备

```bash
git clone <your-fork-url>
cd open_deep_research
uv venv
```

激活虚拟环境：

- macOS / Linux

```bash
source .venv/bin/activate
```

- Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
uv sync
```

### 2) 配置 .env

```bash
cp .env.example .env
```

至少先配置：

```bash
OPENAI_API_KEY=你的key
TAVILY_API_KEY=你的key
LANGSMITH_API_KEY=你的key
LANGSMITH_TRACING=true
```

### 3) 启动本地服务

```bash
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
```

启动后入口：

- API: http://127.0.0.1:2024
- Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- API Docs: http://127.0.0.1:2024/docs

### 4) 最小可运行示例

在 Studio 的 messages 输入：

```text
请用中文简洁回答，不要表格。分析一下 2026 年 AI Agent 在企业落地的关键约束。
```

再追问一个相关问题，检查同线程是否保持偏好风格。

## 本地知识库（RAG）

### 支持格式

- md
- txt
- pdf
- docx

### 构建索引

```bash
python -m open_deep_research.ingestion --source ./knowledge --rebuild
```

- --rebuild：先清空旧索引再重建
- 不加 --rebuild：增量更新（同路径文档会替换，不重复堆叠）

### 启用 RAG

在 .env 中设置：

```bash
RAG_ENABLED=true
LOCAL_KNOWLEDGE_BASE_PATH=./knowledge
VECTOR_STORE_PROVIDER=chroma
CHROMA_PERSIST_DIRECTORY=.chroma
EMBEDDING_MODEL=openai:text-embedding-3-small
RAG_TOP_K=5
```

### 常见问题排查

- 目录不存在：检查 --source 路径
- PDF 或 DOCX 解析失败：安装 pymupdf、python-docx
- 检索为空：确认 ingestion 返回 status=ok 且索引目录存在

## 记忆能力（会话 + 长期）

### 会话记忆（短期）

- 同线程记录临时偏好和关键上下文
- 典型效果：第二轮回答继承第一轮风格约束

### 长期记忆（跨线程）

- 默认策略 explicit_confirmation
- 只有用户明确确认后，候选偏好才写入长期记忆
- 可使用“confirm memory / 确认记忆”触发确认写入

### 推荐开关

```bash
MEMORY_ENABLED=true
MEMORY_WRITE_POLICY=explicit_confirmation
MEMORY_MAX_CANDIDATES_PER_TURN=3
MEMORY_NAMESPACE_PREFIX=memory
USER_ID=demo-user-001
```

## 配置速查表（高频）

| 配置项 | 说明 | 常见值 |
|---|---|---|
| RAG_ENABLED | 是否启用本地 RAG | true / false |
| LOCAL_KNOWLEDGE_BASE_PATH | 本地资料目录 | ./knowledge |
| CHROMA_PERSIST_DIRECTORY | Chroma 持久化目录 | .chroma |
| EMBEDDING_MODEL | 向量化模型 | openai:text-embedding-3-small |
| RAG_TOP_K | 每次检索 chunk 数 | 5 |
| MEMORY_ENABLED | 是否启用记忆能力 | true / false |
| MEMORY_WRITE_POLICY | 长期记忆写入策略 | explicit_confirmation |
| MEMORY_MAX_CANDIDATES_PER_TURN | 每轮候选记忆上限 | 3 |
| MEMORY_NAMESPACE_PREFIX | 记忆命名空间前缀 | memory |
| USER_ID | 本地测试用户标识 | 自定义字符串 |
| memory_mode | API 运行时记忆模式 | off/session_only/long_term_only/both |
| rag_scope | API 运行时 RAG 范围 | disabled/local_only/hybrid |

说明：

- memory_mode、rag_scope 是运行时参数（可通过 API configurable 传入）
- memory_enabled、rag_enabled 是总开关，关闭后会覆盖对应子能力

## 验证与评测

### 本地快速验收

```bash
python tests/pr1_pr3_acceptance/validate_pr1_pr3.py
python tests/pr4_acceptance/validate_pr4.py
python tests/pr5_acceptance/validate_pr5.py
python tests/pr6_acceptance/validate_pr6.py
python tests/pr7_acceptance/validate_pr7.py
python tests/pr8_acceptance/validate_pr8.py
```

Windows 也可以：

```powershell
./tests/pr1_pr3_acceptance/run_acceptance.ps1
```

### 评测入口

```bash
python tests/run_evaluate.py
```

如需跑 RAG/Memory 回归矩阵：

```bash
ODR_PR8_MATRIX=true
python tests/run_evaluate.py
```

## 项目结构（核心）

```text
src/open_deep_research/deep_researcher.py   # 主流程与调度
src/open_deep_research/ingestion.py         # 本地知识库构建
src/open_deep_research/rag.py               # 本地检索工具
src/open_deep_research/configuration.py     # 配置定义与校验
src/open_deep_research/state.py             # 状态定义
tests/pr1_pr3_acceptance/                   # RAG 基础验收
tests/pr4_acceptance/                       # 会话记忆验收
tests/pr5_acceptance/                       # 长期记忆验收
tests/pr6_acceptance/                       # 三通道融合验收
tests/pr7_acceptance/                       # memory_mode/rag_scope 验收
tests/pr8_acceptance/                       # 评测扩展验收
```

## 注意事项

- 这是研究助手，不是事实保证系统，关键结论请结合来源复核
- 全量评测会产生明显 token 成本，建议先跑本地验收再跑大规模评估
- 如需同步上游，请按需与 langchain-ai/open_deep_research 对齐

## 致谢

- Upstream: langchain-ai/open_deep_research
- 本项目在其基础上增强了 RAG、Memory 与评测闭环
