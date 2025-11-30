# Model Court

基于法庭隐喻的多模型集成框架，用于事实核查和内容验证。

## 项目简介

Model Court 使用法庭审判的方式进行 AI 内容验证：

- 检察官：预处理案件，查询历史判例
- 陪审团：多个独立的 LLM 评估员
- 法官：汇总投票，给出最终判决
- 判例库：存储历史判决，支持缓存和相似搜索

## 核心特性

- 多模型集成：使用多个 LLM 提高判断准确性
- STEEL 框架：支持迭代式证据收集
- 判例系统：自动缓存历史判决，避免重复评估
- 可插拔架构：轻松集成自定义 LLM 和参考资料源
- 多种证据源：网络搜索、RAG 知识库、自定义文档
- 灵活配置：自定义判决规则和评估标准

## 快速开始

### 安装

```bash
# 安装核心包（最小依赖）
pip install model-court

# 或安装完整版（包含所有LLM、RAG、搜索功能）
pip install model-court[full]

# 开发版安装（从源码）
pip install -e .
pip install -e .[full]  # 完整版
```

> **注意**：包名是 `model-court`（带连字符），但导入时使用 `model_court`（下划线）

### 基础使用

```python
import asyncio
import os
from model_court import Court, Prosecutor, Jury, Judge
from model_court.code import SqliteCourtCode
from model_court.references import SimpleTextStorage, LocalRAGReference

async def main():
    # 1. 初始化判例库
    court_code = SqliteCourtCode(
        db_path="./fact_check_history.db",
        enable_vector_search=True  # 启用向量检索查找相似判例
    )
    
    # 2. 初始化检察官（启用自动claim拆分）
    prosecutor = Prosecutor(
        court_code=court_code,
        auto_claim_splitting=True,  # 自动拆分复杂陈述
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-3.5-turbo",
            "temperature": 0.1
        },
        prosecutor_prompt="你是一名严格的检察官。请将输入的案情（Case）拆解为独立的、可验证的事实断言（Claims）。"
    )
    
    # 3. 组建陪审团（4个陪审员，不同模型+不同参考资料）
    
    # 陪审员1: 逻辑审查员 (盲审) - GPT-4
    jury_logic = Jury(
        name="Logic_Checker_GPT4",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-4",
            "temperature": 0.0
        },
        reference=None,  # 盲审：不使用外部参考资料
        jury_prompt="请仅根据逻辑一致性和常识判断此 Claim 是否成立，不要编造事实。"
    )
    
    # 陪审员2: 网络侦探 - Perplexity Sonar (自带联网搜索)
    jury_web = Jury(
        name="Web_Detective_Perplexity",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "perplexity/sonar",
            "temperature": 0.0
        },
        reference=None,  # Perplexity模型自带联网搜索能力
        jury_prompt="""You are a research engine. You MUST perform a web search for every claim to provide the most current information. Do not answer from your internal training data. Always cite your sources.

请严格遵守输出规范，你的最终结论（decision）必须且只能是以下三个短语之一：
1. "no_objection" (如果网络证据支持该说法)
2. "suspicious_fact" (如果证据不足或有冲突)
3. "reasonable_doubt" (如果网络证据直接反驳该说法)

你必须基于实时网络搜索的结果进行判断。"""
    )
    
    # 陪审员3: 档案管理员 (RAG) - Llama 3
    jury_rag = Jury(
        name="Archive_Keeper_Llama",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "meta-llama/llama-3-70b-instruct",
            "temperature": 0.2
        },
        reference=LocalRAGReference(
            collection_name="common_rumors",
            persist_directory="./rag_db_storage",
            source_folder="./rumor_txt_files",  # 确保此文件夹存在并包含txt文件
            embedding_model="MiniLM",  # 本地embedding模型
            mode="append",
            top_k=2
        ),
        jury_prompt="请在本地谣言库中检索是否存在匹配的记录。"
    )
    
    # 陪审员4: 基础事实检查员 - GPT-3.5 + 文本存储
    # 从文件读取基础事实知识
    from pathlib import Path
    basic_facts_file = Path("./data/rag_documents/basic_facts.txt")
    with open(basic_facts_file, "r", encoding="utf-8") as f:
        basic_facts_text = f.read()
    
    jury_facts = Jury(
        name="Facts_Checker_GPT35",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-3.5-turbo",
            "temperature": 0.1
        },
        reference=SimpleTextStorage(text=basic_facts_text),
        jury_prompt="""对照提供的基础事实知识，判断此 Claim 是否符合事实。
你的最终结论（decision）必须且只能是以下三个之一：
1. "no_objection"
2. "suspicious_fact"
3. "reasonable_doubt"
"""
    )
    
    # 4. 初始化法官
    judge = Judge(
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-4",
            "temperature": 0.2
        }
    )
    
    # 5. 组建法庭
    court = Court(
        prosecutor=prosecutor,
        juries=[jury_logic, jury_web, jury_rag, jury_facts],  # 4个陪审员
        judge=judge,
        verdict_rules={
            "supported": {"operator": "eq", "value": 0},    # 0个反对票
            "suspicious": {"operator": "lt", "value": 0.5}, # 反对票<50%
            "refuted": "default"  # 其他情况（>=50%反对票）
        },
        quorum=3,  # 至少3个陪审员成功返回
        concurrency_limit=4  # 并发限制
    )
    
    # 6. 进行审理
    case_text = "地球是平的。"
    print(f"🏛️  Model Court 开庭受理中...\nCase: {case_text}")
    
    report = await court.hear(case_text)
    
    # 7. 查看结果
    print("\n" + "="*50)
    print(f"📜 判决意见书 (Case ID: {report.case_id})")
    print("="*50)
    
    for idx, claim_result in enumerate(report.claims, 1):
        print(f"\n🔹 指控 {idx}: {claim_result.claim.text}")
        
        # 展示陪审团投票详情
        print("   [陪审团投票]")
        for vote in claim_result.jury_votes:
            icon = "✅" if vote.decision == "no_objection" else "❌"
            print(f"     {icon} {vote.jury_name}: {vote.decision}")
            if vote.reason:
                print(f"        Reason: {vote.reason[:60]}...")
        
        # 展示最终判决
        print(f"   ⚖️  最终判决: 【{claim_result.verdict.upper()}】")
        print(f"   📝 法官综述: {claim_result.judge_reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 使用 OpenRouter（推荐）

OpenRouter 提供统一接口访问多个 LLM，只需一个 API Key：

```python
# 设置环境变量
export OPENROUTER_API_KEY="sk-or-v1-..."

# 在代码中使用
model_config = {
    "provider": "openai_compatible",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model_name": "openai/gpt-4",  # 或其他模型
}
```

支持的模型：https://openrouter.ai/models

## 支持的 LLM Provider

| Provider | 说明 | 模型示例 |
|---------|------|---------|
| `openai` | 原生 OpenAI API | gpt-4, gpt-3.5-turbo |
| `google` | Google Gemini | gemini-pro, gemini-1.5-pro |
| `anthropic` | Anthropic Claude | claude-3-5-sonnet, claude-3-opus |
| `openai_compatible` | OpenAI兼容API（**推荐**） | 通过OpenRouter访问所有模型 |
| `custom` | 自定义Provider | 本地模型或自建服务 |

**推荐使用 `openai_compatible` + OpenRouter**：
- 一个API Key访问100+模型
- 统一的接口和计费
- 包括 GPT-4、Claude、Gemini、Llama等

## 支持的参考资料源

| Reference类型 | 说明 | 适用场景 |
|-------------|------|---------|
| `SimpleTextStorage` | 纯文本文档 | 简单的事实列表、规则说明 |
| `LocalRAGReference` | 本地RAG知识库 | 大量文档的语义检索 |
| `GoogleSearchReference` | Google自定义搜索 | 需要联网验证最新信息 |
| `None` | 盲审模式 | 纯逻辑推理，不依赖外部资料 |

### Reference 配置示例

**1. 简单文本存储**
```python
from model_court.references import SimpleTextStorage
from pathlib import Path

# 从文件读取
facts_file = Path("./data/rag_documents/basic_facts.txt")
with open(facts_file, "r", encoding="utf-8") as f:
    facts_text = f.read()

reference = SimpleTextStorage(text=facts_text)

# 或者直接传入文本（用于简单测试）
# reference = SimpleTextStorage(text="事实1: 地球是圆的\n事实2: 水的化学式是H2O")
```

**2. 本地RAG知识库**
```python
from model_court.references import LocalRAGReference

reference = LocalRAGReference(
    collection_name="my_knowledge",
    persist_directory="./vector_db",
    source_folder="./documents",  # 包含txt/md文件的文件夹
    embedding_model="MiniLM",  # "MiniLM", "BGE", "OpenAI"
    mode="append",  # "overwrite", "append", "read_only"
    top_k=3  # 返回前3个最相关的文档片段
)
```

**3. Google搜索**
```python
from model_court.references import GoogleSearchReference

reference = GoogleSearchReference(
    api_key="your-google-api-key",
    search_engine_id="your-search-engine-id",
    num_results=5
)
```

**4. 盲审模式（不使用参考资料）**
```python
jury = Jury(
    name="Logic_Checker",
    model=model_config,
    reference=None,  # 不提供参考资料
    jury_prompt="仅根据逻辑和常识判断"
)
```

## 项目结构

```
model_court/
├── model_court/           # 核心包
│   ├── core/             # 核心组件
│   │   ├── models.py     # 数据模型
│   │   ├── court.py      # Court 主类
│   │   ├── prosecutor.py # Prosecutor 类
│   │   ├── jury.py       # Jury 类
│   │   └── judge.py      # Judge 类
│   ├── llm/              # LLM Provider 层
│   │   ├── base.py       # 抽象基类
│   │   ├── openai_provider.py
│   │   ├── google_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── custom_provider.py
│   │   └── factory.py    # Provider 工厂
│   ├── references/       # 参考资料源
│   │   ├── base.py       # 抽象基类
│   │   ├── google_search.py
│   │   ├── web_search.py
│   │   ├── rag_reference.py
│   │   └── text_storage.py
│   ├── embeddings/       # Embedding 模型
│   │   ├── base.py       # 抽象基类
│   │   ├── minilm.py
│   │   ├── bge.py
│   │   └── openai_embedding.py
│   ├── code/             # Court Code 判例库
│   │   ├── base.py       # 抽象基类
│   │   └── sqlite_code.py
│   └── utils/            # 工具函数
│       └── helpers.py
├── example/              # 使用示例
│   ├── example_full.py   # 命令行完整示例
│   ├── backend/          # Web API 服务器
│   ├── frontend/         # Web 前端界面
│   └── data/             # 示例数据
├── api_docs.md           # API 文档
├── README.md             # 项目说明
├── CHANGELOG.md          # 更新日志
├── CONTRIBUTING.md       # 贡献指南
├── LICENSE               # 许可证
├── pyproject.toml        # 项目配置
├── setup.py              # 安装脚本
└── requirements.txt      # 依赖列表
```

## 完整示例

完整的使用示例请查看：
- [命令行完整示例](example/example_full.py) - 展示所有功能的命令行脚本
- [Web应用示例](example/backend/app.py) - 带Web界面的事实核查应用
- [示例文档](example/README.md) - 详细的示例说明和使用指南

## 文档

- [API 文档](api_docs.md) - 完整的 API 参考和示例
- [安装指南](INSTALLATION.md) - 详细的安装和配置说明
- [示例应用](example/) - Web 应用和命令行示例
- [更新日志](CHANGELOG.md) - 版本更新记录
- [贡献指南](CONTRIBUTING.md) - 如何为项目做贡献

## 系统架构

```
案件输入 → 检察官 → [陪审员1, 陪审员2, ..., 陪审员N] → 法官 → 判决结果
              ↓                    ↓
          判例库                参考资料
        (历史判决)            (证据来源)
```

## 高级功能

### 自定义判决规则

根据业务需求自定义判决逻辑：

```python
# 示例1: 严格模式（一票否决）
court_strict = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    verdict_rules={
        "supported": {"operator": "eq", "value": 0},    # 必须0个反对票
        "refuted": "default"  # 任何反对票都判为refuted
    }
)

# 示例2: 宽松模式（少数服从多数）
court_lenient = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    verdict_rules={
        "supported": {"operator": "lt", "value": 0.25},   # 反对票<25%
        "suspicious": {"operator": "lt", "value": 0.75},  # 反对票<75%
        "refuted": "default"  # 反对票>=75%
    }
)

# 示例3: 三档评级
court_detailed = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    verdict_rules={
        "clearly_true": {"operator": "eq", "value": 0},     # 0个反对
        "likely_true": {"operator": "lt", "value": 0.3},    # <30%反对
        "uncertain": {"operator": "lt", "value": 0.6},      # <60%反对
        "likely_false": {"operator": "lt", "value": 0.9},   # <90%反对
        "clearly_false": "default"  # >=90%反对
    }
)
```

### 自动Claim拆分

对于复杂陈述，可以自动拆分为多个独立的claim：

```python
prosecutor = Prosecutor(
    court_code=court_code,
    auto_claim_splitting=True,  # 启用自动拆分
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model_name": "openai/gpt-3.5-turbo",
    },
    prosecutor_prompt="将案情拆解为独立的、可验证的事实断言。"
)

# 输入: "地球是平的，而且太阳绕着地球转。"
# 自动拆分为:
# Claim 1: "地球是平的"
# Claim 2: "太阳绕着地球转"
```

### 判例缓存系统

自动缓存历史判决，避免重复评估：

```python
court_code = SqliteCourtCode(
    db_path="./court_history.db",
    enable_vector_search=True,  # 向量检索相似判例
    default_validity_period=timedelta(days=30)  # 判例有效期
)

# 首次检查: 完整流程，耗时10-30秒
report1 = await court.hear("地球是平的")

# 再次检查相同内容: 直接返回缓存结果，耗时<1秒
report2 = await court.hear("地球是平的")
```

## 使用场景

- **事实核查**：判断新闻、社交媒体内容的真实性
- **内容审核**：检测违规、有害或误导性内容
- **知识问答**：验证AI生成答案的准确性
- **学术研究**：多模型集成提高结论可靠性
- **合规检查**：验证内容是否符合特定规则或标准

## 开发

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/LogicGate-AI-Lab/model-court.git
cd model-court/model_court

# 安装开发版本（包含开发工具）
pip install -e .[dev]

# 或安装完整版（用于运行示例）
pip install -e .[full]
```

### 运行示例

```bash
# 进入示例目录
cd example

# 安装示例依赖
pip install -r requirements.txt

# 配置API Key（复制并编辑.env文件）
cp env.example .env
# 编辑.env，填入OPENROUTER_API_KEY

# 运行命令行示例
python example_full.py

# 运行Web应用示例
cd backend
python app.py
# 浏览器访问 http://localhost:5000
```

### 测试

```bash
# 运行测试（待实现）
pytest

# 代码格式化
black .
ruff check .

# 类型检查
mypy model_court
```

### 项目结构

详见上方"项目结构"部分。核心代码在 `model_court/` 目录下：

- `core/` - 核心组件（Court, Prosecutor, Jury, Judge）
- `llm/` - LLM Provider 抽象层
- `references/` - 参考资料源
- `embeddings/` - Embedding 模型
- `code/` - 判例库系统
- `utils/` - 工具函数

## 常见问题

### Q: 包名和导入名称不一致？

A: 是的，这是有意设计的：
- **安装时**使用 `pip install model-court`（PyPI包名，带连字符）
- **导入时**使用 `from model_court import ...`（Python模块名，下划线）

这是Python常见做法，因为Python模块名不能包含连字符。

### Q: ModuleNotFoundError: No module named 'model_court'

A: 请确保正确安装了包：
```bash
# 在项目根目录（包含 pyproject.toml 的目录）
pip install -e .

# 或从PyPI安装
pip install model-court
```

### Q: 如何使用不同的LLM？

A: 推荐使用 OpenRouter 统一接口：
```python
model_config = {
    "provider": "openai_compatible",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model_name": "模型名称",  # 如 openai/gpt-4, anthropic/claude-3-5-sonnet
}
```

支持的模型列表：https://openrouter.ai/models

### Q: 如何减少API成本？

A: 建议：
1. 使用判例缓存系统（自动避免重复查询）
2. 减少陪审员数量
3. 使用更便宜的模型（如 gpt-3.5-turbo）
4. 禁用自动claim拆分（`auto_claim_splitting=False`）

### Q: 检查速度慢怎么办？

A: 正常情况下，多个AI模型并发评估需要10-30秒。加速方法：
- 使用判例缓存（相同内容第二次检查<1秒）
- 减少陪审员数量
- 选择响应更快的模型
- 调整 `concurrency_limit` 参数

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

MIT License

## 引用

如果您在研究中使用 Model Court，请引用：

```bibtex
@software{modelcourt2024,
  title={Model Court: A Multi-Model Ensemble Framework for Verification},
  author={Model Court Contributors},
  year={2024},
  url={https://github.com/LogicGate-AI-Lab/model-court}
}
```
