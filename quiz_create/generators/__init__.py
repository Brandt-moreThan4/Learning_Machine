"""
Quiz generators module.

This module provides different implementations for generating quiz questions
from text content using various LLM providers.
"""

from quiz_create.generators.base import BaseQuizGenerator
from quiz_create.generators.local_llm import LocalLLMGenerator
from quiz_create.generators.open_ai import OpenAIGenerator
