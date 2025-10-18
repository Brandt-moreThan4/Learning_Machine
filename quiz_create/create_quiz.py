import constants
from pathlib import Path
import json
import random

import quiz_create.generators.prompts as prompts
import quiz_create.generators.local_llm as local_llm


class Question:
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str):
        self.question = question
        self.answer = answer
        self.justification_span = justification_span
        self.difficulty = difficulty

class MCQQuestion(Question):
    def __init__(self, question: str, answer: str, justification_span: str, difficulty: str, distractors: list):
        super().__init__(question, answer, justification_span, difficulty)
        self.distractors = distractors

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
    
    @classmethod
    def from_quiz_data_dict(cls, quiz_data: dict, input_file: Path):
        questions = []
        for q_data in quiz_data.get('questions', []):
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
        """Convert quiz to text format"""
        lines = []
        lines.append(f"Quiz generated from: {self.input_file.name}")
        lines.append("=" * 50)
        lines.append("")
        
        for i, question in enumerate(self.questions, 1):
            lines.append(f"Question {i}: {question.question}")
            lines.append(f"Difficulty: {question.difficulty}")
            lines.append("")
            
            if isinstance(question, MCQQuestion):
                lines.append("Options:")
                all_options = [question.answer] + question.distractors
                # Shuffle options for better quiz experience
                random.shuffle(all_options)
                for j, option in enumerate(all_options, 1):
                    lines.append(f"  {j}. {option}")
            else:
                lines.append(f"Answer: {question.answer}")
            
            lines.append("")
            lines.append(f"Justification: {question.justification_span}")
            lines.append("-" * 30)
            lines.append("")
        
        return "\n".join(lines)
    
    def as_markdown(self) -> str:
        """Convert quiz to markdown format"""
        lines = []
        lines.append(f"# Quiz: {self.input_file.stem}")
        lines.append("")
        lines.append(f"*Generated from: {self.input_file.name}*")
        lines.append("")
        
        for i, question in enumerate(self.questions, 1):
            lines.append(f"## Question {i}")
            lines.append("")
            lines.append(f"**Difficulty:** {question.difficulty.title()}")
            lines.append("")
            lines.append(f"{question.question}")
            lines.append("")
            
            if isinstance(question, MCQQuestion):
                lines.append("**Options:**")
                lines.append("")
                all_options = [question.answer] + question.distractors
                # Shuffle options for better quiz experience
                random.shuffle(all_options)
                for j, option in enumerate(all_options, 1):
                    lines.append(f"{j}. {option}")
            else:
                lines.append(f"**Answer:** {question.answer}")
            
            lines.append("")
            lines.append(f"**Justification:** {question.justification_span}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def as_html(self) -> str:
        """Convert quiz to HTML format"""
        html_lines = []
        html_lines.append("<!DOCTYPE html>")
        html_lines.append("<html lang='en'>")
        html_lines.append("<head>")
        html_lines.append("    <meta charset='UTF-8'>")
        html_lines.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_lines.append(f"    <title>Quiz: {self.input_file.stem}</title>")
        html_lines.append("    <style>")
        html_lines.append("        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }")
        html_lines.append("        .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }")
        html_lines.append("        .question { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }")
        html_lines.append("        .difficulty { color: #666; font-style: italic; }")
        html_lines.append("        .options { margin: 10px 0; }")
        html_lines.append("        .options li { margin: 5px 0; }")
        html_lines.append("        .answer { background-color: #e8f5e8; padding: 10px; border-radius: 3px; margin: 10px 0; }")
        html_lines.append("        .justification { background-color: #f0f8ff; padding: 10px; border-radius: 3px; margin: 10px 0; }")
        html_lines.append("    </style>")
        html_lines.append("</head>")
        html_lines.append("<body>")
        html_lines.append(f"    <div class='header'>")
        html_lines.append(f"        <h1>Quiz: {self.input_file.stem}</h1>")
        html_lines.append(f"        <p><em>Generated from: {self.input_file.name}</em></p>")
        html_lines.append("    </div>")
        
        for i, question in enumerate(self.questions, 1):
            html_lines.append(f"    <div class='question'>")
            html_lines.append(f"        <h2>Question {i}</h2>")
            html_lines.append(f"        <p class='difficulty'>Difficulty: {question.difficulty.title()}</p>")
            html_lines.append(f"        <p>{question.question}</p>")
            
            if isinstance(question, MCQQuestion):
                html_lines.append("        <div class='options'>")
                html_lines.append("            <p><strong>Options:</strong></p>")
                html_lines.append("            <ol>")
                all_options = [question.answer] + question.distractors
                # Shuffle options for better quiz experience
                random.shuffle(all_options)
                for option in all_options:
                    html_lines.append(f"                <li>{option}</li>")
                html_lines.append("            </ol>")
                html_lines.append("        </div>")
            else:
                html_lines.append(f"        <div class='answer'>")
                html_lines.append(f"            <p><strong>Answer:</strong> {question.answer}</p>")
                html_lines.append("        </div>")
            
            html_lines.append(f"        <div class='justification'>")
            html_lines.append(f"            <p><strong>Justification:</strong> {question.justification_span}</p>")
            html_lines.append("        </div>")
            html_lines.append("    </div>")
        
        html_lines.append("</body>")
        html_lines.append("</html>")
        
        return "\n".join(html_lines)
    
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

        self.save_html()
        self.save_markdown()
        self.save_txt()
        
        # if format_type == "html":
        #     return self.save_html()
        # elif format_type == "markdown":
        #     return self.save_markdown()
        # elif format_type == "txt":
        #     return self.save_txt()
        # else:
        #     print(f"Unknown format '{format_type}', defaulting to HTML")
        #     return self.save_html()

    

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
    quiz_data = local_llm.create_quiz_data(source_text, prompt)

    # Process the quiz_data to create Quiz and Question objects
    quiz = Quiz.from_quiz_data_dict(quiz_data, file_path)

    return quiz


if __name__ == "__main__":
    test_file = constants.CLEANED_EMAIL_DATA_DIR / "Morning_Brew__2025-10-16___In_a_jam__199ec791b7c1dd7b.json"

    quiz = create_quiz(test_file)
    
    # Display quiz content
    print("Generated Quiz:")
    print(quiz.as_txt())
    
    # Save quiz to file (defaults to HTML)
    quiz.save()
    
    # Example of saving in different formats:
    # quiz.save("markdown")  # Save as markdown
    # quiz.save("txt")      # Save as text
    # quiz.save("html")     # Save as HTML (default)