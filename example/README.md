# Model Court 示例

本目录包含两个独立的示例，展示如何使用 Model Court 进行事实核查。

**✨ 所有示例统一使用 OpenRouter，只需要一个 API Key！**

## 目录结构

```
example/
├── example_full.py          # 命令行完整示例
├── backend/app.py           # Web API 服务器
├── frontend/index.html      # Web 前端界面
├── data/rag_documents/      # RAG 知识库示例文档
└── requirements.txt         # 额外依赖
```

---

## 示例 1：命令行版本

`example_full.py` 是一个完整的命令行示例，展示所有功能。

### 特点

- 完整的配置示例（检察官、陪审团、法官）
- 多个陪审员使用不同的 LLM 和参考资料
- 支持 DuckDuckGo 开源搜索、RAG 本地知识库
- 演示自动 claim 拆分
- 演示 STEEL 框架（迭代式证据收集）

### 使用方法

```bash
# 1. 安装依赖
cd example
pip install -r requirements.txt

# 2. 配置 API Keys
# 方法 A: 复制 env.example 为 .env 并填入你的 keys (推荐)
cp env.example .env
# 编辑 .env 文件，填入你的 API keys

# 方法 B: 设置环境变量
# Windows PowerShell:
$env:OPENAI_API_KEY="sk-..."
# Linux/Mac:
export OPENAI_API_KEY="sk-..."

# 3. 运行
python example_full.py
```

### 配置说明

文件中包含三个陪审员示例（**全部使用 OpenRouter**）：

1. **Logic_Checker_GPT4** - GPT-4 纯逻辑推理（不使用外部资料）
2. **Web_Detective_Gemini** - Gemini Pro 1.5 + DuckDuckGo 开源搜索 + STEEL 框架
3. **Archive_Keeper_Llama** - Llama 3 70B + 本地 RAG 知识库

**特性：**
- 只需一个 OpenRouter API Key
- 使用 DuckDuckGo 免费开源搜索（无需额外配置）

你可以根据需要修改配置，比如：
- 更改使用的模型（参考 https://openrouter.ai/models）
- 增加或减少陪审员
- 调整判决规则
- 修改测试案例

---

## 示例 2：Web 应用版本

一个带 Web 界面的事实核查应用。

### 特点

- 美观的 Web 界面
- 简化的配置（4 个陪审员）
- 实时显示判决结果
- 自动判例缓存
- 包含 RAG 知识库示例

### 使用方法

#### 步骤 1：设置 API Keys

**方法 A: 使用 .env 文件 (推荐)**

```bash
# 复制示例文件
cp env.example .env

# 编辑 .env 文件，填入你的实际 keys
# 至少需要设置 OPENAI_API_KEY
```

**方法 B: 环境变量**

Windows (PowerShell):
```powershell
$env:OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

Linux/Mac:
```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

#### 步骤 2：安装依赖

```bash
cd example
pip install -r requirements.txt
```

#### 步骤 3：启动服务器

```bash
cd backend
python app.py
```

服务器将在 `http://localhost:5000` 启动。

#### 步骤 4：使用 Web 界面

1. 在浏览器打开 `http://localhost:5000`
2. 在文本框输入需要检查的内容
3. 点击"开始检查"
4. 等待 10-30 秒查看结果

### Web 应用配置

应用使用 4 个陪审员（**全部通过 OpenRouter**）：

1. **GPT-4 Logic** - 逻辑推理（无外部资料）
2. **Gemini WebSearch** - DuckDuckGo 开源搜索 + STEEL 框架
3. **Claude RAG** - 本地知识库查询
4. **Llama Facts** - 基础事实对照

**特性：**
- 只需一个 OpenRouter API Key
- 使用 DuckDuckGo 免费开源搜索（无需额外配置）

可在 `backend/app.py` 的 `initialize_court()` 函数中修改配置。

### 生成的文件

运行后会自动生成：

- `backend/court_history.db` - SQLite 判例数据库
- `data/rag_storage/` - ChromaDB 向量数据库

可使用 SQLite 工具查看判例：

```bash
sqlite3 backend/court_history.db
SELECT * FROM court_code LIMIT 5;
```

---

## RAG 知识库

`data/rag_documents/` 包含两个示例文档：

- `common_myths.txt` - 常见谣言知识
- `scientific_facts.txt` - 科学事实知识

### 添加自定义文档

将 `.txt` 或 `.md` 文件放入 `data/rag_documents/`，重启服务器会自动加载。

---

## 依赖说明

### 核心依赖

```bash
pip install modelcourt  # 或从源码安装：pip install -e ..
pip install python-dotenv  # 自动加载 .env 文件
```

### 额外依赖

- `flask` - Web 服务器（仅 Web 版本需要）
- `flask-cors` - CORS 支持（仅 Web 版本需要）

所有依赖在 `requirements.txt` 中，一键安装：

```bash
pip install -r requirements.txt
```

### API Key

**只需要一个 OpenRouter API Key！**

获取地址：https://openrouter.ai/keys （注册即送免费额度）

---

## 常见问题

### 问题：ModuleNotFoundError: No module named 'modelcourt'

**解决方案：**

```bash
# 在项目根目录（有 pyproject.toml 的目录）
cd ..
pip install -e .

# 或安装完整版
pip install -e .[full]
```

### 问题：所有陪审员都失败

**原因：** 缺少 API Key

**解决方案：** 设置 `OPENROUTER_API_KEY` 环境变量

### 问题：RAG 初始化失败

**解决方案：**
- 确保 `data/rag_documents/` 目录存在
- 检查磁盘空间
- 确认文档文件格式正确

### 问题：检查速度慢

**说明：** 多个 AI 模型并发评估需要 10-30 秒是正常的

**加速方法：**
- 减少陪审员数量
- 使用更快的模型（gpt-3.5-turbo）
- 禁用 STEEL 搜索模式
- 利用判例缓存（相同内容第二次很快）

---

## 对比两个示例

| 特性 | 命令行版本 | Web 版本 |
|------|-----------|----------|
| 使用方式 | Python 脚本 | Web 界面 |
| 配置复杂度 | 高（完整示例） | 低（简化配置） |
| API Keys | 只需 OpenRouter | 只需 OpenRouter |
| 适用场景 | 学习完整功能 | 快速测试 |
| 陪审员数量 | 3 个（可自定义） | 4 个（可修改） |
| 使用的模型 | GPT-4, Gemini, Llama | GPT-4, Gemini, Claude, Llama |
| 结果展示 | 命令行输出 | Web 界面 |

建议：
- 学习功能：使用命令行版本
- 快速测试：使用 Web 版本
- 集成到应用：参考命令行版本的代码

**所有示例都只需要一个 OpenRouter API Key！**

---

## 进一步开发

### 修改陪审员配置

编辑 `backend/app.py` 或 `example_full.py`，在 juries 列表中添加：

```python
juries.append(Jury(
    name="Custom_Jury",
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "model_name": "anthropic/claude-3-5-sonnet",  # 或其他 OpenRouter 支持的模型
        "api_key": os.getenv("OPENROUTER_API_KEY")
    },
    reference=your_reference
))
```

**OpenRouter 支持的模型：** https://openrouter.ai/models

### 修改判决规则

在 Court 初始化时设置：

```python
verdict_rules={
    "clearly_true": {"operator": "eq", "value": 0},
    "likely_true": {"operator": "lt", "value": 0.3},
    "uncertain": {"operator": "lt", "value": 0.6},
    "clearly_false": "default"
}
```

### API 调用

Web 版本提供 REST API：

```bash
curl -X POST http://localhost:5000/api/check \
  -H "Content-Type: application/json" \
  -d '{"text":"地球是平的"}'
```

---

## 相关文档

- [API 完整文档](../api_docs.md)
- [项目主页](../README.md)
- [更新日志](../CHANGELOG.md)

---

## 许可证

MIT License
