"""Reference source implementations for evidence retrieval."""

from .base import BaseReference
from .google_search import GoogleSearchReference
from .rag_reference import LocalRAGReference
from .text_storage import SimpleTextStorage

__all__ = [
    "BaseReference",
    "GoogleSearchReference",
    "LocalRAGReference",
    "SimpleTextStorage",
]

