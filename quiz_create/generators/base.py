"""
Abstract base class for quiz generators.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging


class BaseQuizGenerator(ABC):
    """Abstract base class for quiz generators."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def create_quiz_data(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Generate quiz data from a prompt.
        
        Args:
            prompt: The prompt to generate quiz questions from
            
        Returns:
            List of question dictionaries with keys:
            - kind: Question type (mcq, cloze, tf, short)
            - question: The question text
            - answer: The correct answer
            - distractors: List of wrong answers (for MCQ)
            - difficulty: Difficulty level (easy, medium, hard)
            - justification_span: Justification text from source
        """
        pass
    
    def validate_quiz_data(self, quiz_data: List[Dict[str, Any]]) -> bool:
        """
        Validate that quiz data has the required structure.
        
        Args:
            quiz_data: List of question dictionaries to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(quiz_data, list):
            self.logger.error("Quiz data must be a list")
            return False
        
        required_fields = ['kind', 'question', 'answer', 'difficulty', 'justification_span']
        valid_kinds = ['mcq', 'cloze', 'tf', 'short']
        valid_difficulties = ['easy', 'medium', 'hard']
        
        for i, question in enumerate(quiz_data):
            if not isinstance(question, dict):
                self.logger.error(f"Question {i} must be a dictionary")
                return False
            
            # Check required fields
            for field in required_fields:
                if field not in question:
                    self.logger.error(f"Question {i} missing required field: {field}")
                    return False
            
            # Validate question kind
            if question['kind'] not in valid_kinds:
                self.logger.error(f"Question {i} has invalid kind: {question['kind']}")
                return False
            
            # Validate difficulty
            if question['difficulty'] not in valid_difficulties:
                self.logger.error(f"Question {i} has invalid difficulty: {question['difficulty']}")
                return False
            
            # Validate MCQ questions have distractors
            if question['kind'] == 'mcq':
                if 'distractors' not in question or not isinstance(question['distractors'], list):
                    self.logger.error(f"MCQ question {i} missing or invalid distractors")
                    return False
        
        return True
