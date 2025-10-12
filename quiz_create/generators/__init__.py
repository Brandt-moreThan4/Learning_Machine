"""
Quiz generator modules for different quiz types.
"""

from .template_first import TemplateFirstGenerator
from .local_llm import LocalLLMGenerator
from .cloud_llm import CloudLLMGenerator

# Registry of available generators
GENERATORS = {
    'template_first': TemplateFirstGenerator,
    'local_llm': LocalLLMGenerator,
    'cloud_llm': CloudLLMGenerator,
}


def get_quiz_generator(generator_type: str, config):
    """Get a quiz generator by type."""
    generator_class = GENERATORS.get(generator_type)
    if generator_class:
        return generator_class(config)
    return None


def list_available_generators():
    """List all available quiz generators."""
    return list(GENERATORS.keys())


__all__ = [
    'TemplateFirstGenerator',
    'LocalLLMGenerator', 
    'CloudLLMGenerator',
    'get_quiz_generator',
    'list_available_generators',
]
