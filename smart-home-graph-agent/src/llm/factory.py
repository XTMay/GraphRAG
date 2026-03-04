"""
LLM Factory
============

Factory Pattern implementation for creating LLM instances.

Supported providers:
- openai:  ChatOpenAI via langchain-openai (cloud, requires OPENAI_API_KEY)
- qwen:   ChatTongyi via dashscope (cloud, requires DASHSCOPE_API_KEY)
- ollama: ChatOllama via langchain-ollama (local, no API key needed)

Environment Variables:
    LLM_PROVIDER:       Which provider to use (default: "openai")
    OPENAI_API_KEY:     OpenAI API key
    OPENAI_MODEL:       OpenAI model name (default: "gpt-4o-mini")
    DASHSCOPE_API_KEY:  DashScope API key for Qwen
    QWEN_MODEL:         Qwen model name (default: "qwen-turbo")
    OLLAMA_BASE_URL:    Ollama server URL (default: "http://localhost:11434")
    OLLAMA_MODEL:       Ollama model name (default: "qwen2.5:7b")

Teaching Points:
- Factory Pattern: One function, multiple object types
- Lazy Imports: Only import what you need → faster startup
- Polymorphism: All LLMs share BaseChatModel.invoke() interface
- Dependency Inversion: Code depends on abstraction, not concrete class
"""

import os
from langchain_core.language_models import BaseChatModel


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """
    Factory function: create an LLM instance based on LLM_PROVIDER env var.

    Args:
        temperature: Controls randomness. 0.0 = deterministic, 1.0 = creative.

    Returns:
        A BaseChatModel instance (ChatOpenAI, ChatTongyi, or ChatOllama).

    Raises:
        ValueError: If provider is unknown or misconfigured.

    Teaching Point:
        This is the Factory Pattern — the caller doesn't need to know
        which concrete class is created. They just call llm.invoke().
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()

    if provider == "openai":
        return _create_openai_llm(temperature)
    elif provider == "qwen":
        return _create_qwen_llm(temperature)
    elif provider == "ollama":
        return _create_ollama_llm(temperature)
    else:
        supported = ", ".join(["openai", "qwen", "ollama"])
        raise ValueError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            f"Supported providers: {supported}"
        )


def get_llm_info() -> dict:
    """
    Get information about the currently configured LLM provider.

    Returns:
        Dict with keys: provider, model, status, detail
        - provider: str — "openai", "qwen", or "ollama"
        - model: str — model name being used
        - status: str — "ok" or "error"
        - detail: str — human-readable status message

    Teaching Point:
        Separating "info" from "creation" lets the UI display
        configuration status without actually instantiating the LLM.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()

    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            return {"provider": "openai", "model": model, "status": "ok",
                    "detail": f"API Key: {masked}"}
        else:
            return {"provider": "openai", "model": model, "status": "error",
                    "detail": "OPENAI_API_KEY not set"}

    elif provider == "qwen":
        model = os.getenv("QWEN_MODEL", "qwen-turbo")
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            return {"provider": "qwen", "model": model, "status": "ok",
                    "detail": f"API Key: {masked}"}
        else:
            return {"provider": "qwen", "model": model, "status": "error",
                    "detail": "DASHSCOPE_API_KEY not set"}

    elif provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return {"provider": "ollama", "model": model, "status": "ok",
                "detail": f"Server: {base_url}"}

    else:
        return {"provider": provider, "model": "N/A", "status": "error",
                "detail": f"Unknown provider '{provider}'"}


# =========================================
# PRIVATE: Provider-specific constructors
# =========================================

def _create_openai_llm(temperature: float) -> BaseChatModel:
    """
    Create OpenAI ChatModel instance.

    Teaching Point:
        Lazy import — 'from langchain_openai import ChatOpenAI'
        only runs when this provider is actually selected.
    """
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required for OpenAI provider. "
            "Set it in your .env file."
        )

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
    )


def _create_qwen_llm(temperature: float) -> BaseChatModel:
    """
    Create Qwen/Tongyi ChatModel instance via DashScope API.

    Requires: pip install dashscope langchain-community

    Teaching Point:
        Qwen (通义千问) is Alibaba's LLM, accessible via DashScope API.
        LangChain's ChatTongyi wraps it with the same BaseChatModel interface.
    """
    from langchain_community.chat_models.tongyi import ChatTongyi

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError(
            "DASHSCOPE_API_KEY environment variable is required for Qwen provider. "
            "Get your key at: https://dashscope.console.aliyun.com/"
        )

    return ChatTongyi(
        model=os.getenv("QWEN_MODEL", "qwen-turbo"),
        dashscope_api_key=api_key,
        temperature=temperature,
    )


def _create_ollama_llm(temperature: float) -> BaseChatModel:
    """
    Create Ollama ChatModel instance for local inference.

    Requires: pip install langchain-ollama
              Ollama running locally with a model pulled

    Teaching Point:
        Ollama runs models locally — no API key needed!
        Great for privacy-sensitive use cases and offline development.
        Trade-off: requires GPU/RAM, models may be less capable.
    """
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
    )
