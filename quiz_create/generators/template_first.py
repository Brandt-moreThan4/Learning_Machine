"""
Template-based quiz generator using predefined question templates.
"""

import logging
import random
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import Config


class TemplateFirstGenerator:
    """Template-based quiz generator."""
    
    def __init__(self, config: Config):
        """Initialize the template generator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Question templates
        self.question_templates = {
            'comprehension': [
                "What is the main topic discussed in this email?",
                "What is the primary purpose of this communication?",
                "What is the key message being conveyed?",
                "What is the main subject of this email?",
                "What is the central theme of this message?"
            ],
            'detail': [
                "According to the email, what specific information is provided about {topic}?",
                "What details are mentioned about {topic}?",
                "What specific facts are stated regarding {topic}?",
                "What information is given about {topic}?",
                "What details does the email provide about {topic}?"
            ],
            'inference': [
                "Based on the email content, what can be inferred about {topic}?",
                "What conclusion can be drawn from the information provided?",
                "What does the email suggest about {topic}?",
                "What implication can be made from this message?",
                "What can be deduced from the email content?"
            ],
            'vocabulary': [
                "What does the term '{term}' mean in the context of this email?",
                "How is '{term}' used in this communication?",
                "What is the meaning of '{term}' as used here?",
                "In this context, what does '{term}' refer to?",
                "What does '{term}' mean in this email?"
            ]
        }
    
    def generate_quiz(self, email_data: Dict[str, Any], num_questions: int = 5) -> Optional[Dict[str, Any]]:
        """Generate a quiz from email data."""
        try:
            content = email_data.get('content', '')
            metadata = email_data.get('metadata', {})
            analysis = email_data.get('analysis', {})
            
            if not content:
                self.logger.error("No content found in email data")
                return None
            
            # Extract key information
            topics = analysis.get('topics', [])
            key_phrases = analysis.get('key_phrases', [])
            
            # Generate questions
            questions = self._generate_questions(content, topics, key_phrases, num_questions)
            
            if not questions:
                self.logger.warning("No questions generated")
                return None
            
            # Create quiz structure
            quiz = {
                'type': 'template_first',
                'title': f"Quiz: {metadata.get('title', 'Email Quiz')}",
                'description': f"Quiz generated from: {metadata.get('subject', 'Email')}",
                'source': metadata.get('title', 'Unknown'),
                'questions': questions,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generator': 'template_first',
                    'source_file': email_data.get('file_name', 'Unknown'),
                    'question_count': len(questions)
                }
            }
            
            self.logger.info(f"Generated quiz with {len(questions)} questions")
            return quiz
            
        except Exception as e:
            self.logger.error(f"Error generating quiz: {str(e)}")
            return None
    
    def _generate_questions(self, content: str, topics: List[str], key_phrases: List[str], num_questions: int) -> List[Dict[str, Any]]:
        """Generate questions using templates."""
        questions = []
        
        # Generate comprehension questions
        comprehension_questions = self._generate_comprehension_questions(content, num_questions // 2)
        questions.extend(comprehension_questions)
        
        # Generate detail questions
        if topics:
            detail_questions = self._generate_detail_questions(content, topics, num_questions // 3)
            questions.extend(detail_questions)
        
        # Generate vocabulary questions
        if key_phrases:
            vocab_questions = self._generate_vocabulary_questions(content, key_phrases, num_questions // 4)
            questions.extend(vocab_questions)
        
        # Shuffle and limit questions
        random.shuffle(questions)
        return questions[:num_questions]
    
    def _generate_comprehension_questions(self, content: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate comprehension questions."""
        questions = []
        templates = self.question_templates['comprehension']
        
        for i in range(min(num_questions, len(templates))):
            template = templates[i]
            
            # Extract potential answers from content
            sentences = self._extract_sentences(content)
            if not sentences:
                continue
            
            # Create question
            question = {
                'question': template,
                'type': 'comprehension',
                'options': self._generate_options_for_comprehension(content, sentences),
                'explanation': f"This question tests your understanding of the main content of the email."
            }
            
            questions.append(question)
        
        return questions
    
    def _generate_detail_questions(self, content: str, topics: List[str], num_questions: int) -> List[Dict[str, Any]]:
        """Generate detail questions about specific topics."""
        questions = []
        templates = self.question_templates['detail']
        
        for i in range(min(num_questions, len(templates), len(topics))):
            template = templates[i]
            topic = topics[i]
            
            # Fill in template
            question_text = template.format(topic=topic)
            
            # Extract relevant sentences
            relevant_sentences = self._find_sentences_about_topic(content, topic)
            
            if not relevant_sentences:
                continue
            
            # Create question
            question = {
                'question': question_text,
                'type': 'detail',
                'options': self._generate_options_for_detail(content, relevant_sentences, topic),
                'explanation': f"This question tests your knowledge of specific details about {topic}."
            }
            
            questions.append(question)
        
        return questions
    
    def _generate_vocabulary_questions(self, content: str, key_phrases: List[str], num_questions: int) -> List[Dict[str, Any]]:
        """Generate vocabulary questions."""
        questions = []
        templates = self.question_templates['vocabulary']
        
        # Filter key phrases to find good vocabulary terms
        vocab_terms = self._extract_vocabulary_terms(content, key_phrases)
        
        for i in range(min(num_questions, len(templates), len(vocab_terms))):
            template = templates[i]
            term = vocab_terms[i]
            
            # Fill in template
            question_text = template.format(term=term)
            
            # Create question
            question = {
                'question': question_text,
                'type': 'vocabulary',
                'options': self._generate_options_for_vocabulary(content, term),
                'explanation': f"This question tests your understanding of the term '{term}' in context."
            }
            
            questions.append(question)
        
        return questions
    
    def _extract_sentences(self, content: str) -> List[str]:
        """Extract sentences from content."""
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _find_sentences_about_topic(self, content: str, topic: str) -> List[str]:
        """Find sentences that mention a specific topic."""
        sentences = self._extract_sentences(content)
        relevant = []
        
        for sentence in sentences:
            if topic.lower() in sentence.lower():
                relevant.append(sentence)
        
        return relevant
    
    def _extract_vocabulary_terms(self, content: str, key_phrases: List[str]) -> List[str]:
        """Extract good vocabulary terms from key phrases."""
        vocab_terms = []
        
        for phrase in key_phrases:
            # Look for terms that might be good for vocabulary questions
            words = phrase.split()
            for word in words:
                if len(word) > 5 and word.isalpha() and word.lower() not in ['the', 'this', 'that', 'with', 'from', 'they', 'have', 'been', 'will', 'would']:
                    vocab_terms.append(word)
        
        return list(set(vocab_terms))[:10]  # Limit to 10 unique terms
    
    def _generate_options_for_comprehension(self, content: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Generate options for comprehension questions."""
        options = []
        
        # Extract key phrases as potential answers
        key_phrases = self._extract_key_phrases(content)
        
        # Create correct answer (main topic)
        main_topic = self._extract_main_topic(content)
        options.append({
            'text': main_topic,
            'correct': True
        })
        
        # Create incorrect answers
        incorrect_phrases = [p for p in key_phrases if p != main_topic][:3]
        for phrase in incorrect_phrases:
            options.append({
                'text': phrase,
                'correct': False
            })
        
        # Shuffle options
        random.shuffle(options)
        return options
    
    def _generate_options_for_detail(self, content: str, relevant_sentences: List[str], topic: str) -> List[Dict[str, Any]]:
        """Generate options for detail questions."""
        options = []
        
        # Extract specific details about the topic
        details = self._extract_details_about_topic(content, topic)
        
        if details:
            # Create correct answer
            correct_detail = details[0]
            options.append({
                'text': correct_detail,
                'correct': True
            })
            
            # Create incorrect answers
            other_details = details[1:3] if len(details) > 1 else []
            for detail in other_details:
                options.append({
                    'text': detail,
                    'correct': False
                })
        
        # Fill with generic options if needed
        while len(options) < 4:
            options.append({
                'text': f"Information about {topic} is not provided",
                'correct': False
            })
        
        # Shuffle options
        random.shuffle(options)
        return options
    
    def _generate_options_for_vocabulary(self, content: str, term: str) -> List[Dict[str, Any]]:
        """Generate options for vocabulary questions."""
        options = []
        
        # Try to find the term in context
        context_sentences = self._find_sentences_about_topic(content, term)
        
        if context_sentences:
            # Extract context clues
            context = context_sentences[0]
            
            # Create correct answer based on context
            correct_meaning = self._infer_meaning_from_context(term, context)
            options.append({
                'text': correct_meaning,
                'correct': True
            })
            
            # Create incorrect answers
            incorrect_meanings = [
                f"A type of {term}",
                f"The opposite of {term}",
                f"A synonym for {term}",
                f"Related to {term}"
            ]
            
            for meaning in incorrect_meanings[:3]:
                options.append({
                    'text': meaning,
                    'correct': False
                })
        else:
            # Fallback options
            options.append({
                'text': f"The meaning of {term} in this context",
                'correct': True
            })
            
            for i in range(3):
                options.append({
                    'text': f"Option {i+1} for {term}",
                    'correct': False
                })
        
        # Shuffle options
        random.shuffle(options)
        return options
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases from content."""
        # Simple key phrase extraction
        sentences = self._extract_sentences(content)
        phrases = []
        
        for sentence in sentences:
            # Extract noun phrases (simple heuristic)
            words = sentence.split()
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                if len(phrase) > 5 and phrase.isalpha():
                    phrases.append(phrase)
        
        return list(set(phrases))[:10]
    
    def _extract_main_topic(self, content: str) -> str:
        """Extract the main topic from content."""
        # Simple topic extraction
        sentences = self._extract_sentences(content)
        if not sentences:
            return "General topic"
        
        # Use the first sentence as main topic
        first_sentence = sentences[0]
        words = first_sentence.split()
        
        # Extract first few words as topic
        if len(words) >= 3:
            return " ".join(words[:3])
        else:
            return first_sentence
    
    def _extract_details_about_topic(self, content: str, topic: str) -> List[str]:
        """Extract specific details about a topic."""
        sentences = self._find_sentences_about_topic(content, topic)
        details = []
        
        for sentence in sentences:
            # Extract key information
            words = sentence.split()
            if len(words) > 5:
                details.append(sentence)
        
        return details[:3]  # Limit to 3 details
    
    def _infer_meaning_from_context(self, term: str, context: str) -> str:
        """Infer meaning of a term from context."""
        # Simple context analysis
        words = context.split()
        term_index = -1
        
        for i, word in enumerate(words):
            if term.lower() in word.lower():
                term_index = i
                break
        
        if term_index >= 0:
            # Extract surrounding words
            start = max(0, term_index - 2)
            end = min(len(words), term_index + 3)
            context_words = words[start:end]
            
            return f"The term '{term}' refers to {' '.join(context_words)}"
        else:
            return f"The term '{term}' as used in this context"
