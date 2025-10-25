"""
Shared data models for quiz creation.
"""
from abc import ABC, abstractmethod
from typing import List, Literal
from pathlib import Path
import random
from logging_config import default_logger
import json
from sqlalchemy import text
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from database.db_connect import create_db_connection

class Question(ABC):
    """Base class for all question types."""
    
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        self.question = question
        self.answer = answer
        self.justification_span = justification_span
        self.difficulty = difficulty
    
    @property
    @abstractmethod
    def shuffled_options(self) -> List[str]:
        """Return shuffled options for the question, empty list for non-MCQ questions."""
        pass
    
    @property
    def question_type(self) -> str:
        """Return the question type as a string."""
        return self.__class__.__name__.replace('Question', '').lower()

    def as_dict(self) -> dict:
        return {
            "kind": self.question_type,
            "question": self.question,
            "answer": self.answer,
            "justification_span": self.justification_span,
            "difficulty": self.difficulty,
            "distractors": getattr(self, 'distractors', []),
        }
class MCQQuestion(Question):
    """Multiple Choice Question."""
    
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str, distractors: List[str]):
        super().__init__(question, answer, justification_span, difficulty)
        self.distractors = distractors
    
    @property
    def shuffled_options(self) -> List[str]:
        """Return shuffled options for MCQ questions."""
        all_options = [self.answer] + self.distractors
        random.shuffle(all_options)
        return all_options


class ClozeQuestion(Question):
    """Cloze (fill-in-the-blank) Question."""
    
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        super().__init__(question, answer, justification_span, difficulty)
    
    @property
    def shuffled_options(self) -> List[str]:
        """Cloze questions don't have options."""
        return []


class TFQuestion(Question):
    """True/False Question."""
    
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        super().__init__(question, answer, justification_span, difficulty)
    
    @property
    def shuffled_options(self) -> List[str]:
        """True/False questions don't need shuffling."""
        return ["True", "False"]


class ShortAnswerQuestion(Question):
    """Short Answer Question."""
    
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        super().__init__(question, answer, justification_span, difficulty)
    
    @property
    def shuffled_options(self) -> List[str]:
        """Short answer questions don't have options."""
        return []


class Quiz:
    """Container for quiz questions and metadata."""
    
    def __init__(self, questions: List[Question]):
        self.questions = questions
        self._template_env = None
    
    @property
    def num_questions(self) -> int:
        """Number of questions in the quiz."""
        return len(self.questions)
    
    @property
    def empty(self) -> bool:
        """Check if quiz is empty."""
        return self.num_questions == 0

    @property
    def template_env(self):
        """Lazy-load Jinja2 environment."""
        if self._template_env is None:
            from jinja2 import Environment, FileSystemLoader
            template_dir = Path(__file__).parent / "templates"
            self._template_env = Environment(loader=FileSystemLoader(template_dir))
        return self._template_env
    
    @classmethod
    def from_quiz_data_dict(cls, quiz_data: List[dict]) -> 'Quiz':
        """Create Quiz from list of question dictionaries."""
        questions = []
        for q_data in quiz_data:
            question_type = q_data.get('kind', '').lower()
            
            if question_type == 'mcq':
                question = MCQQuestion(
                    question=q_data['question'],
                    answer=q_data['answer'],
                    justification_span=q_data['justification_span'],
                    difficulty=q_data['difficulty'],
                    distractors=q_data.get('distractors', [])
                )
            elif question_type == 'cloze':
                question = ClozeQuestion(
                    question=q_data['question'],
                    answer=q_data['answer'],
                    justification_span=q_data['justification_span'],
                    difficulty=q_data['difficulty']
                )
            elif question_type == 'tf':
                question = TFQuestion(
                    question=q_data['question'],
                    answer=q_data['answer'],
                    justification_span=q_data['justification_span'],
                    difficulty=q_data['difficulty']
                )
            elif question_type == 'short':
                question = ShortAnswerQuestion(
                    question=q_data['question'],
                    answer=q_data['answer'],
                    justification_span=q_data['justification_span'],
                    difficulty=q_data['difficulty']
                )
            else:
                # Default to short answer if type is unknown
                default_logger.warning('UNKNOWN QUESTION TYPE, DEFAULTING TO SHORT ANSWER')
                question = ShortAnswerQuestion(
                    question=q_data['question'],
                    answer=q_data['answer'],
                    justification_span=q_data['justification_span'],
                    difficulty=q_data['difficulty']
                )
            
            questions.append(question)
        
        return cls(questions)
    
    
    
    def as_html(self) -> str:
        """Convert quiz to HTML format using template."""
        template = self.template_env.get_template('quiz.html')
        return template.render(quiz=self)
    
    
    def save_html(self) -> Path:
        """Save quiz to HTML file."""
        import constants
        constants.QUIZ_OUTPUT_DIR.mkdir(exist_ok=True)
        
        input_stem = self.input_file.stem
        output_file = constants.QUIZ_OUTPUT_DIR / f"{input_stem}_quiz.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.as_html())
        
        default_logger.info(f"Quiz saved to: {output_file}")
        return output_file
    
    def save(self, format_type: str = "html") -> Path:
        """
        Default save method that saves in the specified format.
        
        Args:
            format_type: Format to save in ("html", "markdown", "txt")
        """
        format_type = format_type.lower()
        
        if format_type == "html":
            return self.save_html()
        else:
            default_logger.warning(f"Unknown format '{format_type}', defaulting to HTML")
            return self.save_html()
    
    def as_json(self) -> str:
        """Convert quiz to JSON string."""
        quiz_dict = self.as_dict()
        quiz_json = json.dumps(quiz_dict, indent=2)
        return quiz_json

    def as_dict(self) -> dict:
    
        return {
            "num_questions": self.num_questions,
            "questions": [question.as_dict() for question in self.questions]
        }

    def upload_to_db(self) -> int:
        """
        Upload quiz to database and return the quiz ID.
        
        Returns:
            int: The ID of the uploaded quiz
            
        Raises:
            Exception: If database connection or upload fails
        """

        

        # Create database connection
        engine = create_db_connection()
        
        # Convert quiz to dictionary format for JSON storage
        quiz_data = self.as_dict()


        with engine.connect() as conn:
            stmt = text("""
                INSERT INTO quiz_app.quizzes (data)
                VALUES (:quiz_data)
                RETURNING id
            """).bindparams(bindparam("quiz_data", type_=JSONB))

            result = conn.execute(stmt, {"quiz_data": quiz_data})  # quiz_data is a dict
            quiz_id = result.scalar_one()
            conn.commit()        

        
        default_logger.info(f"Quiz uploaded to database with ID: {quiz_id}")
        return quiz_id


class EmailContent:
    """Container for email content and metadata."""
    
    def __init__(self, input_file:Path):
        self.raw_input_file = input_file

        # The file name should give us some info about the email
        file_meta_data = self.raw_input_file.stem.split("__")
        self.sender = file_meta_data[0]
        self.date = file_meta_data[1]
        self.subject = file_meta_data[2]
        self.drive_id = file_meta_data[-1]
        
    
    def as_dict(self) -> dict:
        return {
            "sender": self.sender,
            "date": self.date,
            "subject": self.subject,
            "drive_id": self.drive_id,
        }
    