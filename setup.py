#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Court Setup Script
安装配置文件，支持传统的 setup.py 方式安装
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取长描述
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="model-court",
    version="0.0.1",
    author="LogicGate AI Lab",
    author_email="contact@logicgate-ai.com",
    description="A multi-model ensemble system using triangular review for fact-checking and verification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LogicGate-AI-Lab/model-court",
    project_urls={
        "Bug Reports": "https://github.com/LogicGate-AI-Lab/model-court/issues",
        "Source": "https://github.com/LogicGate-AI-Lab/model-court",
        "Documentation": "https://github.com/LogicGate-AI-Lab/model-court#readme",
        "Changelog": "https://github.com/LogicGate-AI-Lab/model-court/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests*", "docs*", "example*", "临时自用文件*"]),
    package_data={
        "model_court": ["py.typed"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.9,<4.0",
    
    # 核心依赖
    install_requires=[
        "pydantic>=2.9.0,<3.0.0",
        "python-dateutil>=2.9.0,<3.0.0",
    ],
    
    # 可选依赖
    extras_require={
        "llm": [
            "openai>=1.54.0,<2.0.0",
            "google-generativeai>=0.8.0,<1.0.0",
            "anthropic>=0.39.0,<1.0.0",
        ],
        "rag": [
            "numpy>=1.26.0,<3.0.0",
            "torch>=2.1.0,<3.0.0",
            "sentence-transformers>=3.0.0,<4.0.0",
            "chromadb>=0.5.0,<0.6.0",
        ],
        "search": [
            "aiohttp>=3.10.0,<4.0.0",
            "httpx>=0.27.0,<1.0.0",
            "duckduckgo-search>=6.0.0,<7.0.0",
        ],
        "full": [
            # LLM
            "openai>=1.54.0,<2.0.0",
            "google-generativeai>=0.8.0,<1.0.0",
            "anthropic>=0.39.0,<1.0.0",
            # RAG
            "numpy>=1.26.0,<3.0.0",
            "torch>=2.1.0,<3.0.0",
            "sentence-transformers>=3.0.0,<4.0.0",
            "chromadb>=0.5.0,<0.6.0",
            # Search
            "aiohttp>=3.10.0,<4.0.0",
            "httpx>=0.27.0,<1.0.0",
            "duckduckgo-search>=6.0.0,<7.0.0",
        ],
        "dev": [
            "pytest>=8.0.0,<9.0.0",
            "pytest-asyncio>=0.23.0,<1.0.0",
            "pytest-cov>=5.0.0,<6.0.0",
            "mypy>=1.11.0,<2.0.0",
            "black>=24.0.0,<25.0.0",
            "ruff>=0.6.0,<1.0.0",
            "ipython>=8.12.0,<9.0.0",
        ],
    },
    
    zip_safe=False,
    include_package_data=True,
)
