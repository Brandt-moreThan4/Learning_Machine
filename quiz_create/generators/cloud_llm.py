"""
Cloud LLM quiz generator using OpenAI or Anthropic APIs.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import Config


class CloudLLMGenerator:
    """Cloud LLM quiz generator using OpenAI or Anthropic."""
    
    def __init__(self, config: Config):
        """Initialize the cloud LLM generator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Check which LLM services are available
        self.openai_available = self._check_openai_availability()
        self.anthropic_available = self._check_anthropic_availability()
        
        if not self.openai_available and not self.anthropic_available:
            self.logger.warning("No cloud LLM services available")
    
    def _check_openai_availability(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            if not self.config.llm.openai_api_key:
                return False
            
            import openai
            openai.api_key = self.config.llm.openai_api_key
            return True
        except Exception as e:
            self.logger.error(f"OpenAI not available: {str(e)}")
            return False
    
    def _check_anthropic_availability(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            if not self.config.llm.anthropic_api_key:
                return False
            
            import anthropic
            return True
        except Exception as e:
            self.logger.error(f"Anthropic not available: {str(e)}")
            return False
    
    def generate_quiz(self, email_data: Dict[str, Any], num_questions: int = 5) -> Optional[Dict[str, Any]]:
        """Generate a quiz using cloud LLM."""
        if not self.openai_available and not self.anthropic_available:
            self.logger.error("No cloud LLM services available")
            return None
        
        try:
            content = email_data.get('content', '')
            metadata = email_data.get('metadata', {})
            
            if not content:
                self.logger.error("No content found in email data")
                return None
            
            # Prepare prompt
            prompt = self._create_quiz_prompt(content, num_questions)
            
            # Generate quiz using available LLM
            quiz_data = None
            if self.openai_available:
                quiz_data = self._call_openai(prompt)
            elif self.anthropic_available:
                quiz_data = self._call_anthropic(prompt)
            
            if not quiz_data:
                self.logger.error("Failed to generate quiz with cloud LLM")
                return None
            
            # Parse and structure quiz
            quiz = self._parse_quiz_response(quiz_data, email_data)
            
            if not quiz:
                self.logger.error("Failed to parse quiz response")
                return None
            
            self.logger.info(f"Generated quiz with {len(quiz.get('questions', []))} questions using cloud LLM")
            return quiz
            
        except Exception as e:
            self.logger.error(f"Error generating quiz with cloud LLM: {str(e)}")
            return None
    
    def _create_quiz_prompt(self, content: str, num_questions: int) -> str:
        """Create a prompt for quiz generation."""
        prompt = f"""
You are an expert quiz generator. Create a quiz based on the following email content.

Email Content:
{content[:3000]}  # Limit content to avoid token limits

Requirements:
- Generate exactly {num_questions} questions
- Each question should have 4 multiple choice options
- Include one correct answer and three plausible incorrect answers
- Questions should test comprehension, analysis, and key details
- Make questions specific to the email content
- Ensure questions are clear and unambiguous

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
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API to generate quiz."""
        try:
            import openai
            
            response = openai.ChatCompletion.create(
                model=self.config.llm.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert quiz generator. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
                top_p=0.9
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error calling OpenAI: {str(e)}")
            return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic API to generate quiz."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.config.llm.anthropic_api_key)
            
            response = client.messages.create(
                model=self.config.llm.anthropic_model,
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Error calling Anthropic: {str(e)}")
            return None
    
    def _parse_quiz_response(self, response: str, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse the quiz response from cloud LLM."""
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
                'generator': 'cloud_llm',
                'model': self.config.llm.openai_model if self.openai_available else self.config.llm.anthropic_model,
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
