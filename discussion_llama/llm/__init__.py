"""
LLM integration module for Discussion-Llama.

This module provides tools for interacting with language models.
"""

from .llm_client import LLMClient, OllamaClient, MockLLMClient, create_llm_client

__all__ = ['LLMClient', 'OllamaClient', 'MockLLMClient', 'create_llm_client'] 