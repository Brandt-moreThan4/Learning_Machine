"""
Quiz generators module.

This module provides different implementations for generating quiz questions
from text content using various LLM providers.
"""

from quiz_create.generators.base import BaseQuizGenerator
from quiz_create.generators.local_llm import LocalLLMGenerator, create_quiz_data as create_quiz_data_local
from quiz_create.generators.open_ai import OpenAIGenerator, create_quiz_data as create_quiz_data_openai

__all__ = [
    'BaseQuizGenerator',
    'LocalLLMGenerator', 
    'OpenAIGenerator',
    'create_quiz_data_local',
    'create_quiz_data_openai'
]
