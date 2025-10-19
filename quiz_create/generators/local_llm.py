import json
import ollama
import time
import logging
from typing import List, Dict, Any
from quiz_create.generators.base import BaseQuizGenerator


class LocalLLMGenerator(BaseQuizGenerator):
    """Quiz generator using local Ollama LLM."""
    
    def __init__(self, model: str = 'llama3.1'):
        super().__init__()
        self.model = model
    
    def create_quiz_data(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generate quiz data using local Ollama LLM.
        
        Args:
            prompt: The prompt to generate quiz questions from
            
        Returns:
            List of question dictionaries or None if generation fails
        """
        self.logger.info("Generating quiz data using local LLM...")
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )
            quiz_data_str = response['response']
            
            # Parse JSON response
            quiz_data = json.loads(quiz_data_str)
            
            # Validate the data structure
            if not self.validate_quiz_data(quiz_data):
                self.logger.error("Generated quiz data failed validation")
                return None
                
            return quiz_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse quiz data from LLM response: {e}")
            self.logger.error(f"Response was: {quiz_data_str}")
            return None
        except Exception as e:
            self.logger.error(f"Error generating quiz data: {e}")
            return None


# Backward compatibility function
def create_quiz_data(prompt: str) -> List[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    
    Args:
        prompt: The prompt to generate quiz questions from
        
    Returns:
        List of question dictionaries or None if generation fails
    """
    generator = LocalLLMGenerator()
    return generator.create_quiz_data(prompt)






if __name__ == "__main__":
    prompt = "Tell me the nights watch oath and explain any historical parallels it might have."


    start_time = time.time()
    response = ollama.generate(
        model='llama3.1',
        prompt=prompt
    )
    end_time = time.time()
    
    from logging_config import default_logger
    default_logger.info(f"Generation took {end_time - start_time:.2f} seconds")
    default_logger.info(response['response'])
    default_logger.info('Done!')