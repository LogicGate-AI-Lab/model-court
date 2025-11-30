# Model Court 安装指南

[![EN](https://img.shields.io/badge/lang-EN-blue)](INSTALLATION.md) [![ZH](https://img.shields.io/badge/lang-ZH-red)](INSTALLATION_zh.md)


## 系统要求

- **Python**: >= 3.9, < 4.0
- **操作系统**: Windows / Linux / macOS
- **推荐**: 使用虚拟环境（venv 或 conda）

## 依赖版本说明

### 核心依赖
- `pydantic>=2.9.0,<3.0.0` - 数据验证
- `python-dateutil>=2.9.0,<3.0.0` - 日期处理

### 科学计算与机器学习
- `numpy>=1.26.0,<3.0.0` - 支持 NumPy 1.26+ 和 2.x
- `torch>=2.1.0,<3.0.0` - PyTorch 深度学习框架
- `sentence-transformers>=3.0.0,<4.0.0` - 句子嵌入模型
- `chromadb>=0.5.0,<0.6.0` - 向量数据库（已支持 NumPy 2.x）

### LLM 提供商
- `openai>=1.54.0,<2.0.0` - OpenAI API SDK
- `google-generativeai>=0.8.0,<1.0.0` - Google Gemini API SDK
- `anthropic>=0.39.0,<1.0.0` - Anthropic Claude API SDK

### 网络与搜索
- `aiohttp>=3.10.0,<4.0.0` - 异步HTTP客户端
- `httpx>=0.27.0,<1.0.0` - 现代HTTP客户端
- `duckduckgo-search>=6.0.0,<7.0.0` - DuckDuckGo 搜索 API

## 安装步骤

### 1. 创建虚拟环境（推荐）

```bash
# 使用 venv
python -m venv .venv

# Windows 激活
.venv\Scripts\activate

# Linux/macOS 激活
source .venv/bin/activate
```

### 2. 安装 Model Court 包

#### 方法 A：开发模式安装（推荐用于开发）

```bash
# 从项目根目录
pip install -e .[full]
```

这将安装所有可选依赖。

#### 方法 B：按需安装

```bash
# 只安装核心依赖
pip install -e .

# 添加 LLM 支持
pip install -e .[llm]

# 添加 RAG 支持
pip install -e .[rag]

# 添加搜索支持
pip install -e .[search]

# 完整安装
pip install -e .[full]
```

#### 方法 C：直接安装依赖（不安装包）

```bash
# 从项目根目录
pip install -r requirements.txt
```

### 3. 运行示例

#### 命令行示例

```bash
cd example
python example_full.py
```

#### Web 应用示例

```bash
cd example
# 安装 Web 应用依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 运行 Web 应用
python backend/app.py
```

## 常见问题

### NumPy 版本问题

如果遇到 NumPy 相关错误，请确保安装的是 NumPy 2.x 或 1.26+：

```bash
pip uninstall numpy -y
pip install "numpy>=2.0.0,<3.0.0"
```

### ChromaDB 兼容性

本项目已更新为支持 ChromaDB 0.5.x，这是最新的稳定版本，完全支持 NumPy 2.x。

如果之前安装过旧版本，请清理后重新安装：

```bash
pip uninstall chromadb -y
pip install "chromadb>=0.5.0,<0.6.0"
```

### 虚拟环境清理

如果遇到依赖冲突，建议删除虚拟环境并重新创建：

```bash
# 删除旧的虚拟环境
rm -rf .venv  # Linux/macOS
rmdir /s .venv  # Windows

# 重新创建
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 重新安装
pip install -e .[full]
```

## 验证安装

运行以下 Python 代码验证安装：

```python
import model_court
print(f"Model Court version: {model_court.__version__}")

# 验证核心组件
from model_court import Court, Prosecutor, Jury, Judge
from model_court.code import SqliteCourtCode
from model_court.references import LocalRAGReference, SimpleTextStorage

print("✅ 所有核心组件导入成功！")
```

## 技术支持

如有问题，请访问：
- GitHub Issues: https://github.com/LogicGate-AI-Lab/model-court/issues
- 文档: https://github.com/LogicGate-AI-Lab/model-court#readme

