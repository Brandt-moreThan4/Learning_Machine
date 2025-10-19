import constants
from pathlib import Path
import json
import random
from jinja2 import Environment, FileSystemLoader, Template

import quiz_create.generators.prompts as prompts
import quiz_create.generators.local_llm as local_llm
import quiz_create.generators.open_ai as open_ai


class Question:
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        self.question = question
        self.answer = answer
        self.justification_span = justification_span
        self.difficulty = difficulty
    
    @property
    def shuffled_options(self):
        """Return shuffled options for MCQ questions, empty list for others"""
        return []

class MCQQuestion(Question):
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str, distractors: list):
        super().__init__(question, answer, justification_span, difficulty)
        self.distractors = distractors
    
    @property
    def shuffled_options(self):
        """Return shuffled options for MCQ questions"""
        all_options = [self.answer] + self.distractors
        random.shuffle(all_options)
        return all_options

class ClozeQuestion(Question):
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        super().__init__(question, answer, justification_span, difficulty)

class TFQuestion(Question):
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        super().__init__(question, answer, justification_span, difficulty)

class ShortAnswerQuestion(Question):
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        super().__init__(question, answer, justification_span, difficulty)


class Quiz:
    def __init__(self, questions: list, input_file: Path):
        self.questions = questions
        self.input_file = input_file
        self._template_env = None
    
    @property
    def num_questions(self):
        return len(self.questions)
    
    @property
    def empty(self):
        return self.num_questions == 0

    @property
    def template_env(self):
        """Lazy-load Jinja2 environment"""
        if self._template_env is None:
            template_dir = Path(__file__).parent / "templates"
            self._template_env = Environment(loader=FileSystemLoader(template_dir))
        return self._template_env
    
    @classmethod
    def from_quiz_data_dict(cls, quiz_data, input_file: Path):
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
                print('WANING: UNKNOWN QUESTION TYPE, DEFAULTING TO SHORT ANSWER')
                question = ShortAnswerQuestion(
                    question=q_data['question'],
                    answer=q_data['answer'],
                    justification_span=q_data['justification_span'],
                    difficulty=q_data['difficulty']
                )
            
            questions.append(question)
        
        return cls(questions, input_file)
    
    def as_txt(self) -> str:
        """Convert quiz to text format using template"""
        template = self.template_env.get_template('quiz.txt')
        return template.render(quiz=self)
    
    def as_markdown(self) -> str:
        """Convert quiz to markdown format using template"""
        template = self.template_env.get_template('quiz.md')
        return template.render(quiz=self)
    
    def as_html(self) -> str:
        """Convert quiz to HTML format using template"""
        template = self.template_env.get_template('quiz.html')
        return template.render(quiz=self)
    
    def save_txt(self):
        """Save quiz to text file"""
        constants.QUIZ_OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Create filename based on input file
        input_stem = self.input_file.stem
        output_file = constants.QUIZ_OUTPUT_DIR / f"{input_stem}_quiz.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.as_txt())
        
        print(f"Quiz saved to: {output_file}")
        return output_file
    
    def save_markdown(self):
        """Save quiz to markdown file"""
        constants.QUIZ_OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Create filename based on input file
        input_stem = self.input_file.stem
        output_file = constants.QUIZ_OUTPUT_DIR / f"{input_stem}_quiz.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.as_markdown())
        
        print(f"Quiz saved to: {output_file}")
        return output_file
    
    def save_html(self):
        """Save quiz to HTML file"""
        constants.QUIZ_OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Create filename based on input file
        input_stem = self.input_file.stem
        output_file = constants.QUIZ_OUTPUT_DIR / f"{input_stem}_quiz.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.as_html())
        
        print(f"Quiz saved to: {output_file}")
        return output_file
    
    def save(self, format_type: str = "html"):
        """
        Default save method that saves in the specified format.
        
        Args:
            format_type: Format to save in ("html", "markdown", "txt")
        """
        format_type = format_type.lower()
        
        if format_type == "html":
            return self.save_html()
        elif format_type == "markdown":
            return self.save_markdown()
        elif format_type == "txt":
            return self.save_txt()
        else:
            print(f"Unknown format '{format_type}', defaulting to HTML")
            return self.save_html()
    


def create_quiz(file_path: Path) -> Quiz:
    """
    Create a quiz from an email file.
    
    Args:
        file_path: Path to the cleaned email JSON file
        
    Returns:
        Quiz object containing the generated questions
    """
    with open(file_path, "r", encoding="utf-8") as f:
        email_data = json.load(f)

    source_text = email_data['email_content']

    prompt = prompts.DEFAULT_PROMPT.format(source=source_text, n=5)

    # Call the generator with the prompt to get questions
    quiz_data = local_llm.create_quiz_data(prompt)

    # Process the quiz_data to create Quiz and Question objects
    if quiz_data is not None:
        quiz = Quiz.from_quiz_data_dict(quiz_data, file_path)
    else:
        quiz = Quiz([], file_path)  # Return empty quiz on failure
    return quiz


if __name__ == "__main__":
    test_file = constants.CLEANED_EMAIL_DATA_DIR / "Morning_Brew__2025-10-16___In_a_jam__199ec791b7c1dd7b.json"

    quiz = create_quiz(test_file)
    
    # Display quiz content
    print("Generated Quiz:")
    
    # Save quiz to file (defaults to HTML)
    if quiz is not None:
        quiz.save()
    
    # Example of saving in different formats:
    # quiz.save("markdown")  # Save as markdown
    # quiz.save("txt")      # Save as text
    # quiz.save("html")     # Save as HTML (default)