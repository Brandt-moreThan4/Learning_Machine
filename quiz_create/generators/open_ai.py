import os
import logging
from typing import Literal, List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI
from quiz_create.generators.base import BaseQuizGenerator


class Question(BaseModel):
    """Pydantic model for OpenAI structured output."""
    kind: Literal["mcq","cloze","tf","short"]
    question: str
    answer: str
    distractors: List[str]  # [] for non-MCQ
    difficulty: Literal["easy","medium","hard"]
    justification_span: str

class QuizData(BaseModel):
    """Pydantic model for OpenAI structured output."""
    questions: List[Question]


class OpenAIGenerator(BaseQuizGenerator):
    """Quiz generator using OpenAI API with structured outputs."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__()
        self.model = model
        self.client = self._get_client()
    
    def _get_client(self) -> OpenAI:
        """Get OpenAI client with API key."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return OpenAI(api_key=api_key)
    
    def create_quiz_data(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generate quiz data using OpenAI API with structured outputs.
        
        Args:
            prompt: The prompt to generate quiz questions from
            
        Returns:
            List of question dictionaries or None if generation fails
        """
        self.logger.info("Generating quiz data using OpenAI LLM (Responses API)...")
        
        try:
            resp = self.client.responses.parse(
                model=self.model,
                input=prompt,
                text_format=QuizData,
            )
            
            # Convert Pydantic model to list of dictionaries
            quiz_data = resp.output_parsed.model_dump()['questions']
            
            # Validate the data structure
            if not self.validate_quiz_data(quiz_data):
                self.logger.error("Generated quiz data failed validation")
                return None
                
            return quiz_data
            
        except Exception as e:
            self.logger.error(f"Error generating quiz data with OpenAI: {e}")
            return None

