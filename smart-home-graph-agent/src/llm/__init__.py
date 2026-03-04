"""
LLM Factory Module
==================

Provides a unified interface to create LLM instances for different providers.

Usage:
    from src.llm import get_llm, get_llm_info

    llm = get_llm(temperature=0.0)       # Returns BaseChatModel
    info = get_llm_info()                 # Returns provider/model info dict

Teaching Point:
    Factory Pattern - one function creates different objects based on config.
    All returned objects share the same interface (BaseChatModel.invoke()).
"""

from src.llm.factory import get_llm, get_llm_info
