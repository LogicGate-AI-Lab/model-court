# Model Court Installation Guide

[![EN](https://img.shields.io/badge/lang-EN-blue)](INSTALLATION.md) [![ZH](https://img.shields.io/badge/lang-ZH-red)](INSTALLATION_zh.md)

## System Requirements

- **Python**: >= 3.9, < 4.0  
- **Operating System**: Windows / Linux / macOS  
- **Recommended**: Use a virtual environment (venv or conda)

## Dependency Overview

### Core Dependencies
- `pydantic>=2.9.0,<3.0.0` – Data validation
- `python-dateutil>=2.9.0,<3.0.0` – Date and time utilities

### Scientific Computing & Machine Learning
- `numpy>=1.26.0,<3.0.0` – Supports NumPy 1.26+ and 2.x
- `torch>=2.1.0,<3.0.0` – PyTorch deep learning framework
- `sentence-transformers>=3.0.0,<4.0.0` – Sentence embedding models
- `chromadb>=0.5.0,<0.6.0` – Vector database (supports NumPy 2.x)

### LLM Providers
- `openai>=1.54.0,<2.0.0` – OpenAI API SDK
- `google-generativeai>=0.8.0,<1.0.0` – Google Gemini API SDK
- `anthropic>=0.39.0,<1.0.0` – Anthropic Claude API SDK

### Networking & Search
- `aiohttp>=3.10.0,<4.0.0` – Asynchronous HTTP client
- `httpx>=0.27.0,<1.0.0` – Modern HTTP client
- `duckduckgo-search>=6.0.0,<7.0.0` – DuckDuckGo Search API

---

## Installation Steps

### 1. Create a Virtual Environment (Recommended)

```bash
# Using venv
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on Linux/macOS
source .venv/bin/activate
```

---

### 2. Install Model Court

#### Method A: Development Mode Install (Recommended for contributors)

```bash
# From project root
pip install -e .[full]
```

This installs all optional dependencies.

#### Method B: Install Only What You Need

```bash
# Core only
pip install -e .

# Add LLM support
pip install -e .[llm]

# Add RAG support
pip install -e .[rag]

# Add search support
pip install -e .[search]

# Full installation
pip install -e .[full]
```

#### Method C: Install dependencies only (without installing package)

```bash
pip install -r requirements.txt
```

---

## 3. Run Examples

### Command Line Example

```bash
cd example
python example_full.py
```

### Web Application Example

```bash
cd example

# Install Web dependencies
pip install -r requirements.txt

# Configure environment variables
cp env.example .env
# Edit .env with your API keys

# Run web app
python backend/app.py
```

---

## Common Issues

### NumPy Version Errors

If you encounter NumPy-related errors, reinstall NumPy 2.x or 1.26+:

```bash
pip uninstall numpy -y
pip install "numpy>=2.0.0,<3.0.0"
```

### ChromaDB Compatibility

This project supports ChromaDB 0.5.x, fully compatible with NumPy 2.x.

If you previously installed older versions:

```bash
pip uninstall chromadb -y
pip install "chromadb>=0.5.0,<0.6.0"
```

### Virtual Environment Cleanup

If dependencies conflict, recreate the venv:

```bash
# Remove old environment
rm -rf .venv      # Linux/macOS
rmdir /s .venv    # Windows

# Recreate
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate     # Linux/macOS

pip install -e .[full]
```

---

## Verify Installation

Run the following Python code:

```python
import model_court
print(f"Model Court version: {model_court.__version__}")

from model_court import Court, Prosecutor, Jury, Judge
from model_court.code import SqliteCourtCode
from model_court.references import LocalRAGReference, SimpleTextStorage

print("✅ All core components imported successfully!")
```

---

## Support

For help or reporting issues:

- GitHub Issues: https://github.com/LogicGate-AI-Lab/model-court/issues
- Documentation: https://github.com/LogicGate-AI-Lab/model-court#readme
