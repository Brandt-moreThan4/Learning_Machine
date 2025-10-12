"""
Local LLM quiz generator using Ollama.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import Config


class LocalLLMGenerator:
    """Local LLM quiz generator using Ollama."""
    
    def __init__(self, config: Config):
        """Initialize the local LLM generator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Check if Ollama is available
        self.ollama_available = self._check_ollama_availability()
        
        if not self.ollama_available:
            self.logger.warning("Ollama not available. Local LLM generation will not work.")
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get(f"{self.config.llm.ollama_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama not available: {str(e)}")
            return False
    
    def generate_quiz(self, email_data: Dict[str, Any], num_questions: int = 5) -> Optional[Dict[str, Any]]:
        """Generate a quiz using local LLM."""
        if not self.ollama_available:
            self.logger.error("Ollama not available")
            return None
        
        try:
            content = email_data.get('content', '')
            metadata = email_data.get('metadata', {})
            
            if not content:
                self.logger.error("No content found in email data")
                return None
            
            # Prepare prompt
            prompt = self._create_quiz_prompt(content, num_questions)
            
            # Generate quiz using Ollama
            quiz_data = self._call_ollama(prompt)
            
            if not quiz_data:
                self.logger.error("Failed to generate quiz with Ollama")
                return None
            
            # Parse and structure quiz
            quiz = self._parse_quiz_response(quiz_data, email_data)
            
            if not quiz:
                self.logger.error("Failed to parse quiz response")
                return None
            
            self.logger.info(f"Generated quiz with {len(quiz.get('questions', []))} questions using Ollama")
            return quiz
            
        except Exception as e:
            self.logger.error(f"Error generating quiz with local LLM: {str(e)}")
            return None
    
    def _create_quiz_prompt(self, content: str, num_questions: int) -> str:
        """Create a prompt for quiz generation."""
        prompt = f"""
You are an expert quiz generator. Create a quiz based on the following email content.

Email Content:
{content[:2000]}  # Limit content to avoid token limits

Requirements:
- Generate exactly {num_questions} questions
- Each question should have 4 multiple choice options
- Include one correct answer and three plausible incorrect answers
- Questions should test comprehension, analysis, and key details
- Make questions specific to the email content

Format your response as JSON with this structure:
{{
    "title": "Quiz Title",
    "description": "Quiz Description",
    "questions": [
        {{
            "question": "Question text?",
            "options": [
                {{"text": "Option A", "correct": true}},
                {{"text": "Option B", "correct": false}},
                {{"text": "Option C", "correct": false}},
                {{"text": "Option D", "correct": false}}
            ],
            "explanation": "Explanation of the correct answer"
        }}
    ]
}}

Generate the quiz now:
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API to generate quiz."""
        try:
            import requests
            
            payload = {
                "model": self.config.llm.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.config.llm.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {str(e)}")
            return None
    
    def _parse_quiz_response(self, response: str, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse the quiz response from Ollama."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                self.logger.error("No JSON found in response")
                return None
            
            json_str = response[json_start:json_end]
            quiz_data = json.loads(json_str)
            
            # Validate quiz structure
            if not self._validate_quiz_structure(quiz_data):
                self.logger.error("Invalid quiz structure")
                return None
            
            # Add metadata
            quiz_data['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'generator': 'local_llm',
                'model': self.config.llm.ollama_model,
                'source_file': email_data.get('file_name', 'Unknown')
            }
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing quiz response: {str(e)}")
            return None
    
    def _validate_quiz_structure(self, quiz_data: Dict[str, Any]) -> bool:
        """Validate the structure of the generated quiz."""
        try:
            # Check required fields
            if 'title' not in quiz_data or 'questions' not in quiz_data:
                return False
            
            # Check questions
            questions = quiz_data.get('questions', [])
            if not isinstance(questions, list) or len(questions) == 0:
                return False
            
            # Check each question
            for question in questions:
                if not isinstance(question, dict):
                    return False
                
                if 'question' not in question or 'options' not in question:
                    return False
                
                options = question.get('options', [])
                if not isinstance(options, list) or len(options) != 4:
                    return False
                
                # Check options
                for option in options:
                    if not isinstance(option, dict):
                        return False
                    
                    if 'text' not in option or 'correct' not in option:
                        return False
                
                # Check that exactly one option is correct
                correct_options = [opt for opt in options if opt.get('correct', False)]
                if len(correct_options) != 1:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating quiz structure: {str(e)}")
            return False
