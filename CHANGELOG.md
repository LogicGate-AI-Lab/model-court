# 更新日志

所有重要变更都会记录在此文件中。

版本格式遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [0.0.1] - 2024-11-30

### 新增功能

核心组件

- Court 主编排器
- Prosecutor 检察官（案件预处理和判例查询）
- Jury 陪审员（独立评估）
- Judge 法官（汇总投票和判决）

LLM Provider 支持

- OpenAI (GPT-3.5, GPT-4)
- Google Gemini
- Anthropic Claude
- 自定义 Provider 接口

参考资料源

- Google Custom Search
- Web Search (DuckDuckGo)
- Local RAG (ChromaDB)
- Simple Text Storage

Embedding 模型

- MiniLM (轻量级)
- BGE-Large (高质量)
- OpenAI Embedding

判例系统

- SQLite 存储结构化数据
- ChromaDB 向量相似度搜索
- 自动缓存历史判决
- 有效期管理

其他功能

- STEEL 框架（迭代式证据收集）
- 自动 Claim 拆分
- 并发评估支持
- 灵活的判决规则配置
- 完整的类型提示支持
- 异步 API
- Web 示例应用

### 文档

- 完整的 API 文档
- 使用示例
- 项目结构说明
- Web 应用示例（Flask + HTML）

### 技术要求

- Python >= 3.9
- 核心依赖: pydantic>=2.9.0, python-dateutil>=2.9.0
- 可选依赖:
  - LLM: openai>=1.54.0, google-generativeai>=0.8.0, anthropic>=0.39.0
  - RAG: numpy>=1.26.0 (支持 2.x), torch>=2.1.0, sentence-transformers>=3.0.0, chromadb>=0.5.0
  - Search: aiohttp>=3.10.0, httpx>=0.27.0, duckduckgo-search>=6.0.0

### 已知限制

- 首次运行需要下载 embedding 模型
- RAG 初始化可能需要几分钟
- 多模型并发评估需要较长时间（10-30秒）

---

## 未来计划

### v0.1.0 (计划中)

- 添加更多 LLM Provider
- 支持批量处理
- 性能优化
- 更多测试用例

### v0.2.0 (计划中)

- Web UI 增强
- 用户认证
- API 限流
- 数据导出功能

---

[0.0.1]: https://github.com/LogicGate-AI-Lab/model-court/releases/tag/v0.0.1
