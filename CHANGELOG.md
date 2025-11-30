# Changelog

A simple and easy-to-maintain changelog.
Follow Semantic Versioning: https://semver.org/

---

## 0.0.2 --- 2025-11-30

**Added** - Example code - Converted project introduction to English

---

## 0.0.1 --- 2025-11-30

**Core Features** - Court (orchestrator) - Prosecutor (preprocessing &
precedent search) - Jury (independent evaluation) - Judge (result
aggregation)

**LLM Providers** - OpenAI (GPT-3.5 / GPT-4) - Google Gemini - Anthropic
Claude - Custom provider interface

**Reference Sources** - Google Custom Search - DuckDuckGo Web Search -
Local RAG (ChromaDB) - Simple text storage

**Embedding Models** - MiniLM - BGE-Large - OpenAI Embeddings

**Precedent System** - SQLite storage - Vector search via ChromaDB -
Auto caching & expiration

**Other Features** - STEEL evidence-gathering loop - Claim splitting -
Concurrent evaluation - Flexible judgment rules - Full type hints -
Async API - Web demo app

**Docs** - API documentation - Usage examples - Project structure - Web
demo (Flask + HTML)

**Requirements** - Python ≥ 3.9\

- Core: pydantic, python-dateutil\
- Optional: OpenAI, Gemini, Anthropic, torch, chromadb,
  duckduckgo-search

**Known Limits** - First run downloads embedding models - RAG init may
take minutes - Concurrent evaluation slower (10--30s)

---

## Future

- More research to improve Model Court reliability and effectiveness.
