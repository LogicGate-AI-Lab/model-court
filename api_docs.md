# Model Court API Documentation

Version: 0.1.0

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Components](#core-components)
4. [LLM Providers](#llm-providers)
5. [Reference Sources](#reference-sources)
6. [Embeddings](#embeddings)
7. [Court Code](#court-code)
8. [Complete Examples](#complete-examples)

---

## Installation

### Basic Installation

```bash
pip install modelcourt
```

### Installation with Optional Dependencies

```bash
# Full installation (all features)
pip install modelcourt[full]

# Or install specific components
pip install modelcourt[openai]        # OpenAI support
pip install modelcourt[google]        # Google Gemini support
pip install modelcourt[anthropic]     # Anthropic Claude support
pip install modelcourt[rag]           # RAG with ChromaDB
pip install modelcourt[search]        # Web search capabilities
pip install modelcourt[embeddings]    # Local embedding models
```

---

## Quick Start

```python
import asyncio
from modelcourt import Court, Prosecutor, Jury, Judge, SqliteCourtCode

# Initialize components
court_code = SqliteCourtCode(db_path="./my_court.db")
prosecutor = Prosecutor(court_code=court_code)

jury = Jury(
    name="GPT-Jury",
    model={"provider": "openai", "model_name": "gpt-4", "api_key": "sk-..."}
)

judge = Judge(
    model={"provider": "openai", "model_name": "gpt-4", "api_key": "sk-..."}
)

court = Court(
    prosecutor=prosecutor,
    juries=[jury],
    judge=judge
)

# Run trial
async def main():
    report = await court.hear("The Earth is flat.")
    print(court.summary(report))

asyncio.run(main())
```

---

## Core Components

### Court

The main orchestrator that coordinates the entire trial process.

#### Constructor

```python
Court(
    prosecutor: Prosecutor,
    juries: List[Jury],
    judge: Judge,
    verdict_rules: Optional[Dict[str, Any]] = None,
    quorum: int = 3,
    concurrency_limit: int = 5
)
```

**Parameters:**
- `prosecutor`: Prosecutor instance for case preprocessing
- `juries`: List of Jury instances (minimum 3 recommended)
- `judge`: Judge instance for rendering verdicts
- `verdict_rules`: Custom rules for determining verdicts (optional)
- `quorum`: Minimum number of successful jury votes required
- `concurrency_limit`: Maximum number of concurrent operations

#### Methods

##### `async hear(case_text: str, domain: str = "general") -> CaseReport`

Conduct a full trial for a case.

**Parameters:**
- `case_text`: The case text to evaluate
- `domain`: Domain of the case (e.g., "fact_check", "finance", "law")

**Returns:** `CaseReport` with results for all claims

##### `summary(report: CaseReport) -> str`

Generate a human-readable summary of the case report.

**Parameters:**
- `report`: Case report to summarize

**Returns:** Summary text string

### Prosecutor

Preprocesses cases and searches for precedents.

#### Constructor

```python
Prosecutor(
    court_code: BaseCourtCode,
    auto_claim_splitting: bool = False,
    model: Optional[Dict[str, Any]] = None,
    prosecutor_prompt: Optional[str] = None
)
```

**Parameters:**
- `court_code`: Court code database for precedent search
- `auto_claim_splitting`: Whether to automatically split cases into claims
- `model`: LLM model configuration (required if auto_claim_splitting is True)
- `prosecutor_prompt`: Custom prompt for claim splitting

#### Methods

##### `async process(case_text: str) -> ProsecutorReport`

Process a case and prepare it for trial.

### Jury

Individual evaluator that assesses claims.

#### Constructor

```python
Jury(
    name: str,
    model: Dict[str, Any],
    reference: Optional[BaseReference] = None,
    jury_prompt: Optional[str] = None,
    search_cycle_mode: bool = False,
    search_cycle_max: int = 3
)
```

**Parameters:**
- `name`: Name/identifier for this jury
- `model`: LLM model configuration
- `reference`: Reference source for evidence (None = blind mode)
- `jury_prompt`: Custom prompt for the jury
- `search_cycle_mode`: Enable STEEL iterative search framework
- `search_cycle_max`: Maximum search cycles (for STEEL)

#### Methods

##### `async vote(claim: Claim) -> JuryVote`

Evaluate a claim and cast a vote.

### Judge

Aggregates jury votes and renders final verdicts.

#### Constructor

```python
Judge(
    model: Dict[str, Any],
    verdict_rules: Optional[Dict[str, Any]] = None,
    judge_prompt: Optional[str] = None
)
```

**Parameters:**
- `model`: LLM model configuration
- `verdict_rules`: Rules for determining verdicts based on votes
- `judge_prompt`: Custom prompt for the judge

**Verdict Rules Example:**
```python
verdict_rules = {
    "supported": {"operator": "eq", "value": 0},      # 0 objections
    "suspicious": {"operator": "lt", "value": 0.5},   # < 50% objections
    "refuted": "default"                               # >= 50% objections
}
```

#### Methods

##### `async verdict(claim: Claim, jury_votes: List[JuryVote], precedents: Optional[List[Precedent]] = None) -> ClaimResult`

Render a verdict for a claim.

---

## LLM Providers

### Model Configuration Format

All LLM configurations use a standard dictionary format:

```python
model_config = {
    "provider": "openai",           # Required: provider name
    "model_name": "gpt-4",          # Required: model name
    "api_key": "sk-...",            # Optional: API key
    "base_url": "...",              # Optional: custom base URL
    "temperature": 0.7,             # Optional: temperature (default 0.7)
    "max_tokens": 1000,             # Optional: max tokens
    "timeout": 60                   # Optional: timeout in seconds
}
```

### Supported Providers

#### OpenAI

```python
model = {
    "provider": "openai",
    "model_name": "gpt-4",  # or "gpt-3.5-turbo", "gpt-4-turbo"
    "api_key": "sk-..."
}
```

#### Google Gemini

```python
model = {
    "provider": "google",  # or "gemini"
    "model_name": "gemini-1.5-pro",  # or "gemini-1.5-flash"
    "api_key": "AIza...",
    "enable_grounding": False  # Optional: enable Google Search
}
```

#### Anthropic Claude

```python
model = {
    "provider": "anthropic",  # or "claude"
    "model_name": "claude-3-5-sonnet-20241022",
    "api_key": "sk-ant-..."
}
```

#### OpenAI-Compatible (Local Models)

```python
model = {
    "provider": "openai_compatible",
    "model_name": "llama-3-70b",
    "base_url": "http://localhost:8000/v1",
    "api_key": "empty"
}
```

### Custom Providers

You can create custom LLM providers:

```python
from modelcourt.llm import BaseLLMProvider, register_provider

class MyCustomProvider(BaseLLMProvider):
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        # Your custom implementation
        return "Generated text"

# Register your provider
register_provider("my_provider", MyCustomProvider)

# Use it
model = {"provider": "my_provider", "model_name": "my-model"}
```

---

## Reference Sources

### SimpleTextStorage

Store reference text directly or load from a file.

```python
from modelcourt.references import SimpleTextStorage

# From text
ref = SimpleTextStorage(text="Reference content here...")

# From file
ref = SimpleTextStorage(file_path="./reference.txt")
```

### WebSearchReference

Free web search using DuckDuckGo.

```python
from modelcourt.references import WebSearchReference

ref = WebSearchReference(
    max_results=5,
    region="wt-wt",  # Worldwide
    safesearch="moderate"
)
```

### GoogleSearchReference

Google Custom Search API.

```python
from modelcourt.references import GoogleSearchReference

ref = GoogleSearchReference(
    api_key="YOUR_GOOGLE_API_KEY",
    cse_id="YOUR_CSE_ID",
    search_depth=3
)
```

### LocalRAGReference

Vector-based RAG with ChromaDB.

```python
from modelcourt.references import LocalRAGReference

ref = LocalRAGReference(
    collection_name="my_knowledge",
    persist_directory="./rag_db",
    embedding_model="MiniLM",  # or "BGE", "OpenAI"
    source_folder="./documents",  # Optional: folder with source docs
    mode="append",  # "overwrite", "append", or "read_only"
    top_k=3
)
```

**Modes:**
- `overwrite`: Delete existing collection and rebuild from source_folder
- `append`: Add documents from source_folder to existing collection
- `read_only`: Only query, don't modify collection

---

## Embeddings

Embedding models are used by RAG and CourtCode for vector similarity.

### MiniLM (Recommended for Most Cases)

```python
embedding_model = "MiniLM"
# Dimension: 384
# Fast, lightweight, good general performance
```

### BGE-Large (Higher Quality)

```python
embedding_model = "BGE"
# Dimension: 1024
# Slower, larger, better quality
```

### OpenAI Embeddings

```python
embedding_model = "OpenAI"
embedding_api_key = "sk-..."
# Requires API key
# Models: text-embedding-3-small (1536), text-embedding-3-large (3072)
```

---

## Court Code

The Court Code stores historical precedents for efficient retrieval.

### SqliteCourtCode

```python
from modelcourt import SqliteCourtCode

court_code = SqliteCourtCode(
    db_path="./court_history.db",
    embedding_model="MiniLM",  # For vector search
    default_validity_period=timedelta(days=30),  # Optional
    enable_vector_search=True
)
```

**Features:**
- Exact match search for identical claims
- Vector similarity search for related claims
- Validity period management
- User-editable SQLite database

### Methods

##### `async search_exact(claim: str) -> Optional[CourtCodeEntry]`

Search for an exact match.

##### `async search_similar(claim: str, top_k: int = 5, threshold: float = 0.7) -> List[Precedent]`

Search for similar claims using vector similarity.

##### `async add_entry(entry: CourtCodeEntry) -> str`

Add a new precedent entry.

---

## Complete Examples

### Example 1: Simple Fact-Checking Court

```python
import asyncio
from modelcourt import Court, Prosecutor, Jury, Judge, SqliteCourtCode

async def simple_fact_check():
    # Initialize court code
    court_code = SqliteCourtCode(db_path="./fact_check.db")
    
    # Create prosecutor (no claim splitting)
    prosecutor = Prosecutor(court_code=court_code)
    
    # Create 3 juries with different models
    juries = [
        Jury(
            name="GPT-4",
            model={
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "sk-..."
            }
        ),
        Jury(
            name="Claude",
            model={
                "provider": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
                "api_key": "sk-ant-..."
            }
        ),
        Jury(
            name="Gemini",
            model={
                "provider": "google",
                "model_name": "gemini-1.5-pro",
                "api_key": "AIza..."
            }
        )
    ]
    
    # Create judge
    judge = Judge(
        model={
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-..."
        }
    )
    
    # Assemble court
    court = Court(
        prosecutor=prosecutor,
        juries=juries,
        judge=judge,
        quorum=2  # Require at least 2 successful votes
    )
    
    # Run trial
    case = "Drinking bleach cures COVID-19."
    report = await court.hear(case, domain="fact_check")
    
    # Print summary
    print(court.summary(report))

asyncio.run(simple_fact_check())
```

### Example 2: Advanced Court with References and STEEL

```python
import asyncio
from datetime import timedelta
from modelcourt import (
    Court, Prosecutor, Jury, Judge, SqliteCourtCode,
    WebSearchReference, LocalRAGReference, SimpleTextStorage
)

async def advanced_court():
    # Initialize court code with validity period
    court_code = SqliteCourtCode(
        db_path="./advanced_court.db",
        embedding_model="BGE",  # Higher quality embeddings
        default_validity_period=timedelta(days=90)
    )
    
    # Create prosecutor with auto claim splitting
    prosecutor = Prosecutor(
        court_code=court_code,
        auto_claim_splitting=True,
        model={
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "sk-..."
        },
        prosecutor_prompt="Break down the case into specific, verifiable claims."
    )
    
    # Create reference sources
    web_search = WebSearchReference(max_results=5)
    
    rag_reference = LocalRAGReference(
        collection_name="medical_facts",
        persist_directory="./medical_rag",
        embedding_model="BGE",
        source_folder="./medical_docs",
        mode="read_only"
    )
    
    text_reference = SimpleTextStorage(
        file_path="./known_facts.txt"
    )
    
    # Create diverse juries
    juries = [
        # Blind jury (no external reference)
        Jury(
            name="Blind_Logic_Checker",
            model={
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "sk-...",
                "temperature": 0.0
            },
            jury_prompt="Evaluate based purely on logical consistency."
        ),
        
        # Web search jury with STEEL framework
        Jury(
            name="Web_Detective",
            model={
                "provider": "google",
                "model_name": "gemini-1.5-pro",
                "api_key": "AIza..."
            },
            reference=web_search,
            search_cycle_mode=True,  # Enable STEEL
            search_cycle_max=3,
            jury_prompt="Find conclusive evidence through web search."
        ),
        
        # RAG jury
        Jury(
            name="Knowledge_Base",
            model={
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "sk-..."
            },
            reference=rag_reference,
            jury_prompt="Check against known medical facts."
        ),
        
        # Text reference jury
        Jury(
            name="Fact_Checker",
            model={
                "provider": "anthropic",
                "model_name": "claude-3-5-sonnet-20241022",
                "api_key": "sk-ant-..."
            },
            reference=text_reference
        )
    ]
    
    # Create judge with custom verdict rules
    judge = Judge(
        model={
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-..."
        },
        verdict_rules={
            "clearly_true": {"operator": "eq", "value": 0},
            "likely_true": {"operator": "lt", "value": 0.25},
            "uncertain": {"operator": "lt", "value": 0.5},
            "likely_false": {"operator": "lt", "value": 0.75},
            "clearly_false": "default"
        }
    )
    
    # Assemble court
    court = Court(
        prosecutor=prosecutor,
        juries=juries,
        judge=judge,
        quorum=3,
        concurrency_limit=4
    )
    
    # Run trial
    case = """
    Recent claims about health:
    1. Vitamin C megadoses prevent all viral infections.
    2. The human body has 206 bones.
    3. Homeopathic remedies are more effective than antibiotics.
    """
    
    report = await court.hear(case, domain="medical_fact_check")
    
    # Print results
    print(court.summary(report))
    
    # Access individual results
    for i, claim_result in enumerate(report.claims, 1):
        print(f"\n=== Claim {i} ===")
        print(f"Text: {claim_result.claim.text}")
        print(f"Verdict: {claim_result.verdict}")
        print(f"Objections: {claim_result.objection_count}/{len(claim_result.jury_votes)}")
        
        for vote in claim_result.jury_votes:
            print(f"  - {vote.jury_name}: {vote.decision} ({vote.confidence:.2f})")

asyncio.run(advanced_court())
```

### Example 3: Custom Provider Integration

```python
from modelcourt.llm import BaseLLMProvider, register_provider
import asyncio

class MyLocalLLMProvider(BaseLLMProvider):
    """Custom provider for local LLM."""
    
    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        # Your custom LLM logic here
        # This could call a local model, custom API, etc.
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        # Example: call your local model
        response = await self._call_local_model(full_prompt)
        return response
    
    async def _call_local_model(self, prompt: str) -> str:
        # Implement your local model call
        pass

# Register the custom provider
register_provider("my_local_llm", MyLocalLLMProvider)

# Use it in Court
jury = Jury(
    name="Local_LLM_Jury",
    model={
        "provider": "my_local_llm",
        "model_name": "my-model",
        "temperature": 0.5
    }
)
```

---

## Data Models

### CaseReport

```python
class CaseReport(BaseModel):
    case_id: str
    case_text: str
    domain: str
    status: Literal["completed", "mistrial", "partial"]
    claims: List[ClaimResult]
    overall_verdict: Optional[str]
    error_message: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
```

### ClaimResult

```python
class ClaimResult(BaseModel):
    claim: Claim
    jury_votes: List[JuryVote]
    verdict: str
    judge_reasoning: str
    objection_count: int
    objection_ratio: float
    timestamp: datetime
```

### JuryVote

```python
class JuryVote(BaseModel):
    jury_name: str
    claim_id: str
    decision: Literal["no_objection", "suspicious_fact", "reasonable_doubt"]
    confidence: float  # 0.0-1.0
    reason: str
    reference_summary: Optional[str]
    search_cycles: int
    timestamp: datetime
```

---

## Best Practices

### 1. Jury Diversity

Use different LLM providers and reference sources for better ensemble performance:

```python
juries = [
    Jury(name="GPT", model=openai_config, reference=None),  # Blind
    Jury(name="Claude", model=claude_config, reference=web_search),
    Jury(name="Gemini", model=gemini_config, reference=rag_db)
]
```

### 2. Appropriate Quorum

Set quorum based on the number of juries:
- 3 juries: quorum=2 (allow 1 failure)
- 5 juries: quorum=3 or 4
- 7+ juries: quorum=5

### 3. Claim Splitting

Enable auto claim splitting for complex cases:

```python
prosecutor = Prosecutor(
    court_code=court_code,
    auto_claim_splitting=True,
    model=cheap_model_config  # Use cheaper model for splitting
)
```

### 4. STEEL Framework

Use STEEL for juries with search capabilities:

```python
jury = Jury(
    name="Searcher",
    model=model_config,
    reference=web_search,
    search_cycle_mode=True,
    search_cycle_max=3
)
```

### 5. Validity Periods

Set appropriate validity periods for time-sensitive domains:

```python
court_code = SqliteCourtCode(
    db_path="./finance_court.db",
    default_validity_period=timedelta(days=7)  # Financial data changes quickly
)
```

---

## Error Handling

All async methods can raise exceptions. Wrap calls in try-except:

```python
try:
    report = await court.hear(case_text)
except Exception as e:
    print(f"Court failed: {e}")
```

Individual jury failures are handled gracefully - failed juries are counted as abstentions.

---

## Performance Tips

1. **Concurrency**: Adjust `concurrency_limit` based on API rate limits
2. **Caching**: Court code automatically caches results for identical claims
3. **Embeddings**: Use MiniLM for speed, BGE for quality
4. **Model Selection**: Use cheaper models for prosecutor, expensive for juries/judge

---

## License

MIT License

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/model-court/issues
- Documentation: https://github.com/yourusername/model-court

---

**Version:** 0.1.0  
**Last Updated:** 2024

