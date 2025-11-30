# Model Court: A Multi-Model Ensemble Framework for Verification

[![EN](https://img.shields.io/badge/lang-EN-blue)](README.md) [![ZH](https://img.shields.io/badge/lang-ZH-red)](README_zh.md)

## Project Overview (V0.0.2)

Model Court is an open-source framework designed to make cross-verification and fact-checking with multiple models easier. **Model Court is inspired by concepts from the U.S. courtroom system, using the roles of Prosecutor, Jury, and Judge to verify facts, with support for internet search, RAG-based retrieval, and more.**  
The current version is **0.0.2**, released on **2025-11-30**, and provides the basic core functionality.

Model Court performs AI content verification using a courtroom-style process:

- **Prosecutor**: Preprocesses the case, queries historical precedents. If a valid precedent already exists and has not expired, the result is returned directly without entering a full trial.
- **Jury**: Multiple independent LLM evaluators. Each juror is independent; it is recommended that each uses different retrieval tools and models from different providers.
- **Judge**: Aggregates votes and produces the final verdict, which is then stored as a precedent in the precedent database.

This courtroom-style process can **improve reliability in scenarios where LLM outputs need to be verified**, such as:

- **Fact-checking**: Determining the factual accuracy of news and social media content.
- **Content moderation**: Detecting harmful, violating, or misleading content.
- **Knowledge Q&A**: Verifying the correctness of AI-generated answers.
- **Academic research**: Improving robustness via multi-model ensemble.
- **Compliance checking**: Verifying whether content complies with certain rules or standards.

**The basic courtroom flow is as follows:**

```
Case Input → Prosecutor → [Juror1, Juror2, ..., JurorN] → Judge → Verdict
                ↓                         ↓
         Precedent Database          Reference Sources
           (Past Rulings)              (Evidence)
```

For the full courtroom process, see the detailed introduction below.

---

Related documents:

- [API Documentation](api_docs.md) – Full API reference and examples  
- [Installation Guide](INSTALLATION.md) – Detailed installation and configuration  
- [Changelog](CHANGELOG.md) – Version history  
- [Contribution Guide](CONTRIBUTING.md) – How to contribute to this project  

## Installation

This project is published on [PyPI](https://pypi.org/project/model-court/) and can be installed via `pip`.

**Install**

```bash
# Install core package (minimal dependencies)
pip install model-court

# Or install the full version (includes all LLM, RAG, search features)
pip install model-court[full]

# Development install (from source)
pip install -e .
pip install -e .[full]  # Full version from source
```

> **Note:** The package name is `model-court` (with a hyphen), but the import name is `model_court` (with an underscore).

---

## Detailed Introduction

### Full Courtroom Workflow

**The full courtroom workflow is as follows:**

```
┌───────────────────────────────────────────┐
│               🏛️ Model Court             │
│              Main Courtroom Flow         │
└───────────────────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │     Input Case Text      │
        └──────────────────────────┘
                     │
                     ▼
   ┌───────────────────────────────────────┐
   │        1. Prosecutor (Prosecutor)     │
   ├───────────────────────────────────────┤
   │ • Optionally split the case into      │
   │   multiple claims (if enabled)        │
   │ • Query precedent DB (SQL + Vector)   │
   │   to avoid redundant evaluation       │
   │     - Cache hit → return past ruling  │
   │     - Similar precedent → provide     │
   │       as reference to the Judge       │
   └───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│     2. Launch Multiple Juries in Parallel   │
└─────────────────────────────────────────────┘
                     │
                     ▼
   ┌──────────────────────────────────────────────┐
   │           🧑‍⚖️  Jury Voting Process           │
   ├──────────────────────────────────────────────┤
   │ Cross-validate claims using independent LLMs │
   │ to reduce hallucinations.                    │
   │ Each jury can focus on different criteria,   │
   │ either purely model-based or using pluggable │
   │ reference sources:                           │
   │                                              │
   │ ① Logical review: evaluate based on logic    │
   │    and common sense only.                    │
   │ ② Web search: validate claims using real-    │
   │    time web search (supports iterative       │
   │    verification).                            │
   │ ③ RAG: use integrated RAG pipeline; Model    │
   │    Court handles creation, embedding, and    │
   │    retrieval.                                │
   │ ④ Text document store: a basic fact store    │
   │    providing textual factual references.     │
   │                                              │
   │ All jury members choose exactly one of:      │
   │      • "no_objection"     (support)          │
   │      • "suspicious_fact"  (insufficient      │
   │                            evidence)         │
   │      • "reasonable_doubt" (counter-evidence) │
   │ Note: if a jury member fails or cannot       │
   │ provide a conclusion, it is counted as       │
   │ "abstains".                                  │
   └──────────────────────────────────────────────┘
                     │
                     ▼
       ┌───────────────────────────────────────┐
       │             3. Judge (Judge)          │
       ├───────────────────────────────────────┤
       │ • Aggregates jury votes               │
       │ • References similar precedents       │
       │ • Rule-based verdict logic; requires  │
       │   reaching a minimum quorum of valid  │
       │   votes                               │
       │       ▶ supported  (no objections)    │
       │       ▶ suspicious (some objections)  │
       │       ▶ refuted   (majority oppose)   │
       │ • Outputs Judge reasoning             │
       └───────────────────────────────────────┘
                     │
                     ▼
     ┌───────────────────────────────────────┐
     │      4. Court Generates CaseReport    │
     ├───────────────────────────────────────┤
     │ • Structured list of claims           │
     │ • Jury votes and rationales           │
     │ • Referenced precedents (if any)      │
     │ • Final judgment                      │
     │ • Persisted into precedent DB         │
     │   (SQL + Vector)                      │
     └───────────────────────────────────────┘

```

### Full Example

You must configure the Prosecutor, Jury, and Judge before you can use Model Court. The setup is simple: specify which models to use and configure their APIs.  
We recommend using **OpenRouter**, which allows you to access many LLMs with a single API key. The system also supports ChatGPT, Gemini, Claude, etc. See later sections for more details.

> **Note: the courtroom process must be run asynchronously.**

```python
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv  # Load .env for environment variables

from model_court import Court, Prosecutor, Jury, Judge
from model_court.code import SqliteCourtCode
from model_court.references import SimpleTextStorage, LocalRAGReference

# Load environment variables
load_dotenv()

# ----------------------------------------------------------------------
# 0. Preparation
# ----------------------------------------------------------------------
# Before running this demo, please make sure you have completed:
#
# 1. Environment configuration (.env)
#    - Create a .env file in the current directory
#    - Add API key, e.g.:
#      OPENROUTER_API_KEY=sk-or-v1-xxxx...
#
# 2. Virtual environment (recommended)
#    - python -m venv .venv
#    - source .venv/bin/activate  (Windows: .venv\Scripts\activate)
#
# 3. Install dependencies
#    - pip install model-court python-dotenv
#    - pip install model-court[full]  # Recommended if using RAG
#
# 4. Prepare data files (paths used in the code; below we use RAG jury
#    and text-based jury as examples)
#    Make sure the directory structure looks like:
#
#    .
#    ├── .env
#    ├── example_court.py (this file)
#    └── data/
#        ├── rag_init_files/           <-- initialization corpus for RAG jury
#        │   └── rumors_2024.txt       (any text files as knowledge base)
#        └── text_documents/           <-- reference files for text-based jury
#            └── basic_facts.txt       (basic factual text such as policies,
#                                      legal clauses, etc.)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# 1. Initialize Court: configure Prosecutor, Juries, and Judge
# ----------------------------------------------------------------------
def build_court() -> Court:
    # 1. Initialize precedent store (persistent storage)
    court_code = SqliteCourtCode(
        db_path="./fact_check_history.db",
        enable_vector_search=True
    )

    # 2. Initialize Prosecutor (check precedents and split claims)
    prosecutor = Prosecutor(
        court_code=court_code,
        auto_claim_splitting=False,  # Set True to split case into multiple claims
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-3.5-turbo",
            "temperature": 0.1
        },
        prosecutor_prompt=(
            "You are a strict prosecutor. Break the input case into "
            "independent, verifiable factual claims."
        )
    )

    # 3. Initialize juries (ensure diversity to keep them independent)

    # [Logical perspective]
    jury_logic = Jury(
        name="Logic_Jury",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-4",
            "temperature": 0.0
        },
        reference=None,
        jury_prompt=(
            "Evaluate whether the statement is reasonable based on logic "
            "and common sense only. Do not fabricate information."
        )
    )

    # [Web search perspective]
    jury_web = Jury(
        name="Web_Jury",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "perplexity/sonar",  # This model has built-in web access
            "temperature": 0.0
        },
        reference=None,
        jury_prompt=(
            "Use web search to verify each claim and base your judgment "
            "on the latest information."
        )
    )

    # [Local RAG perspective]
    jury_rag = Jury(
        name="RAG_Jury",
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
            source_folder="./data/rag_init_files",
            embedding_model="MiniLM",
            mode="append",
            top_k=2
        ),
        jury_prompt="Query the local rumor knowledge base to see if related records exist."
    )

    # [Text document perspective]
    basic_facts_path = Path("./data/text_documents/basic_facts.txt")

    # Basic file check for demo convenience
    if not basic_facts_path.exists():
        raise FileNotFoundError(
            f"Demo failed: please create file {basic_facts_path} first."
        )

    jury_facts = Jury(
        name="Facts_Jury",
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-3.5-turbo",
            "temperature": 0.1
        },
        reference=SimpleTextStorage(text=basic_facts_path.read_text(encoding="utf-8")),
        jury_prompt="Compare each claim against the basic facts text to decide if it is true."
    )

    # 4. Initialize Judge
    judge = Judge(
        model={
            "provider": "openai_compatible",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": "openai/gpt-4",
            "temperature": 0.2
        }
    )

    # 5. Assemble the Court
    return Court(
        prosecutor=prosecutor,
        juries=[jury_logic, jury_web, jury_rag, jury_facts],
        judge=judge,
        verdict_rules={
            "supported": {"operator": "eq", "value": 0},
            "suspicious": {"operator": "lt", "value": 0.5},
            "refuted": "default"
        },
        quorum=3,
        concurrency_limit=4
    )


# ----------------------------------------------------------------------
# 2. Run a demo
# ----------------------------------------------------------------------
async def demo():
    # Instantiate the court; RAG models will be loaded on first run
    court = build_court()

    # Case input
    case_text = "China and the United States have already had diplomatic relations for 300 years, and the two governments held a celebration for this."

    # Hear the case asynchronously
    report = await court.hear(case_text)

    # Display contents of the Report object
    print(f"
{'='*20} Case Report (ID: {report.case_id}) {'='*20}")

    for i, res in enumerate(report.claims, 1):
        print(f"
[Claim {i}] {res.claim.text}")

        # Print detailed jury votes
        for vote in res.jury_votes:
            print(f"  - {vote.jury_name}: {vote.decision}")
            if vote.reason:
                print(f"    Reason: {vote.reason[:60]}...")

        print(f"
  => Judge Verdict: [{res.verdict}]")
        print(f"  => Judge Reasoning: {res.judge_reasoning}")

    print(f"
{'='*60}")


if __name__ == "__main__":
    # The court process must be run asynchronously
    asyncio.run(demo())
```

More examples can be found under the `example` folder in the project:

- [Full CLI example](example/example_full.py) – Command-line script demonstrating all major features (similar to the example above).  
- [Web app example](example/backend/app.py) – A fact-checking web application that shows how to integrate Model Court into a web UI.

## Project Configuration

### LLM

The project supports the following LLM providers:

| Provider              | Description                          | Example Models                      |
| --------------------- | ------------------------------------ | ----------------------------------- |
| `openai`              | Native OpenAI API                    | gpt-4, gpt-3.5-turbo                |
| `google`              | Google Gemini                        | gemini-pro, gemini-1.5-pro          |
| `anthropic`           | Anthropic Claude                     | claude-3-5-sonnet, claude-3-opus    |
| `openai_compatible`   | OpenAI-compatible API (**recommended**) | Access all models via OpenRouter |
| `custom`              | Custom provider                      | Local models or self-hosted service |

**Recommended: `openai_compatible` + OpenRouter**

OpenRouter provides a unified interface to many LLMs. With a single API key, you can access over 100 models, including some that are free (e.g., deepseek).

```python
# Environment variable
export OPENROUTER_API_KEY="sk-or-v1-..."

# In code
model_config = {
    "provider": "openai_compatible",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model_name": "openai/gpt-4",  # Or any other supported model
}
```

Supported models list: https://openrouter.ai/models

### Reference

The project supports the following built-in reference sources and modes:

| Reference Type          | Description        | Typical Use Case                     |
| ----------------------- | ------------------ | ------------------------------------ |
| `SimpleTextStorage`     | Plain text docs    | Simple fact lists, rule descriptions |
| `LocalRAGReference`     | Local RAG KB       | Semantic search over large corpora   |
| `GoogleSearchReference` | Google Custom Search | Need real-time web verification   |
| `None`                  | Blind mode         | Pure logical reasoning without external sources |

**1. Simple text storage**

```python
from model_court.references import SimpleTextStorage
from pathlib import Path

# Read from file
facts_file = Path("./data/rag_documents/basic_facts.txt")
with open(facts_file, "r", encoding="utf-8") as f:
    facts_text = f.read()

reference = SimpleTextStorage(text=facts_text)

# Or directly pass a small text block (for quick tests)
# reference = SimpleTextStorage(text="Fact 1: The Earth is round
Fact 2: The chemical formula of water is H2O")
```

**2. Local RAG knowledge base**

```python
from model_court.references import LocalRAGReference

reference = LocalRAGReference(
    collection_name="my_knowledge",
    persist_directory="./vector_db",
    source_folder="./documents",  # Folder with txt/md files
    embedding_model="MiniLM",     # "MiniLM", "BGE", or "OpenAI"
    mode="append",                # "overwrite", "append", or "read_only"
    top_k=3                       # Return top 3 most relevant chunks
)
```

**3. Google Search**

```python
from model_court.references import GoogleSearchReference

reference = GoogleSearchReference(
    api_key="your-google-api-key",
    search_engine_id="your-search-engine-id",
    num_results=5
)
```

**4. Blind mode (no reference)**

```python
jury = Jury(
    name="Logic_Checker",
    model=model_config,
    reference=None,  # No external references
    jury_prompt="Judge only based on logic and common sense."
)
```

## Project Structure

```text
model_court/
├── model_court/             # Core package
│   ├── core/                # Core components
│   │   ├── models.py        # Data models
│   │   ├── court.py         # Court main class
│   │   ├── prosecutor.py    # Prosecutor class
│   │   ├── jury.py          # Jury class
│   │   └── judge.py         # Judge class
│   ├── llm/                 # LLM provider layer
│   │   ├── base.py          # Abstract base classes
│   │   ├── openai_provider.py
│   │   ├── google_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── custom_provider.py
│   │   └── factory.py       # Provider factory
│   ├── references/          # Reference sources
│   │   ├── base.py          # Abstract base classes
│   │   ├── google_search.py
│   │   ├── web_search.py
│   │   ├── rag_reference.py
│   │   └── text_storage.py
│   ├── embeddings/          # Embedding models
│   │   ├── base.py          # Abstract base classes
│   │   ├── minilm.py
│   │   ├── bge.py
│   │   └── openai_embedding.py
│   ├── code/                # Court Code (precedent store)
│   │   ├── base.py          # Abstract base classes
│   │   └── sqlite_code.py
│   └── utils/               # Helper utilities
│       └── helpers.py
├── example/                 # Usage examples
│   ├── example_full.py      # Full CLI example
│   ├── backend/             # Web API server
│   ├── frontend/            # Web frontend
│   └── data/                # Example data
├── api_docs.md              # API documentation
├── README.md                # Project description
├── CHANGELOG.md             # Changelog
├── CONTRIBUTING.md          # Contribution guide
├── LICENSE                  # License
├── pyproject.toml           # Project configuration
├── setup.py                 # Setup script
└── requirements.txt         # Dependencies
```

.

## Advanced Features

### Custom Verdict Rules

You can customize verdict rules according to your business requirements:

```python
# Example 1: Strict mode (single veto)
court_strict = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    verdict_rules={
        "supported": {"operator": "eq", "value": 0},   # Must have 0 opposing votes
        "refuted": "default"  # Any opposing vote → refuted
    }
)

# Example 2: Lenient mode (majority rule)
court_lenient = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    verdict_rules={
        "supported": {"operator": "lt", "value": 0.25},   # Opposition < 25%
        "suspicious": {"operator": "lt", "value": 0.75},  # Opposition < 75%
        "refuted": "default"  # Opposition >= 75%
    }
)

# Example 3: Multi-level rating
court_detailed = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    verdict_rules={
        "clearly_true": {"operator": "eq", "value": 0},     # 0 opposition
        "likely_true": {"operator": "lt", "value": 0.3},    # < 30% opposition
        "uncertain": {"operator": "lt", "value": 0.6},      # < 60% opposition
        "likely_false": {"operator": "lt", "value": 0.9},   # < 90% opposition
        "clearly_false": "default"  # >= 90% opposition
    }
)
```

### Automatic Claim Splitting

For complex statements, you can automatically split them into multiple independent claims:

```python
prosecutor = Prosecutor(
    court_code=court_code,
    auto_claim_splitting=True,  # Enable auto splitting
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model_name": "openai/gpt-3.5-turbo",
    },
    prosecutor_prompt="Split the case into independent, verifiable factual claims."
)

# Input: "The Earth is flat, and the Sun orbits the Earth."
# Automatically split into:
# Claim 1: "The Earth is flat."
# Claim 2: "The Sun orbits the Earth."
```

### Precedent Caching System

Automatically cache past rulings to avoid repeated evaluation:

```python
from datetime import timedelta

court_code = SqliteCourtCode(
    db_path="./court_history.db",
    enable_vector_search=True,              # Vector search for similar cases
    default_validity_period=timedelta(days=30)  # Precedent validity period
)

# First check: full pipeline, typically 10–30 seconds
report1 = await court.hear("The Earth is flat.")

# Second check with same content: directly return cached result, < 1 second
report2 = await court.hear("The Earth is flat.")
```

## FAQ

### Q: Why are the package name and import name different?

This is intentional:

- **Installation**: `pip install model-court` (PyPI package name, with hyphen)  
- **Import**: `from model_court import ...` (Python module name, with underscore)

This is a common pattern in Python because module names cannot contain hyphens.

### Q: I get `ModuleNotFoundError: No module named 'model_court'`

Please ensure the package is installed correctly:

```bash
# From project root (where pyproject.toml is located)
pip install -e .

# Or install from PyPI
pip install model-court
```

### Q: How do I use different LLMs?

Recommended: use OpenRouter as a unified entrypoint:

```python
model_config = {
    "provider": "openai_compatible",
    "base_url": "https://openrouter.ai/api/v1",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "model_name": "MODEL_NAME",  # e.g., openai/gpt-4, anthropic/claude-3-5-sonnet
}
```

Supported model list: https://openrouter.ai/models

You can of course also use the official APIs for ChatGPT, Gemini, Claude, or school/corporate APIs that are OpenAI-compatible.

### Q: How can I reduce API costs?

Suggestions:

1. Use cheaper or free APIs when possible.  
2. Use smaller or local models (local inference is supported).  
3. Use the precedent caching system to avoid repeated evaluation.  
4. Reduce the number of juries.  
5. Use cheaper models such as `gpt-3.5-turbo`.  
6. Disable automatic claim splitting (`auto_claim_splitting=False`).

### Q: What if evaluation is slow?

Normally, evaluating multiple models in parallel takes about **10–30 seconds**. To speed up:

- Enable and leverage precedent caching (second run on the same content is < 1 second).  
- Reduce the number of juries.  
- Choose faster models.  
- Tune the `concurrency_limit` parameter.

## License & Citation

This project is licensed under the MIT License and can be used freely, including for commercial purposes.

If you use Model Court in your research, please cite:

```bibtex
@software{model-court,
  title={Model Court: A Multi-Model Ensemble Framework for Verification},
  author={Jeff Liu},
  year={2025},
  url={https://github.com/LogicGate-AI-Lab/model-court}
}
```
