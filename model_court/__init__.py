"""
Model Court - A multi-model ensemble framework for fact-checking and verification.

Core Components:
- Court: Main orchestrator
- Prosecutor: Case preprocessing and claim splitting
- Jury: Individual model evaluators
- Judge: Final verdict aggregator
"""

__version__ = "0.0.1"

# Core components
from model_court.core import Court, Prosecutor, Jury, Judge
from model_court.code import SqliteCourtCode
from model_court.references import (
    GoogleSearchReference,
    LocalRAGReference,
    SimpleTextStorage
)
from model_court.llm import BaseLLMProvider, create_llm_provider

__all__ = [
    "Court",
    "Prosecutor",
    "Jury",
    "Judge",
    "SqliteCourtCode",
    "GoogleSearchReference",
    "LocalRAGReference",
    "SimpleTextStorage",
    "BaseLLMProvider",
    "create_llm_provider",
]

