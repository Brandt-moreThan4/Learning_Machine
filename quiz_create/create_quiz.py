import constants
from pathlib import Path
from bs4 import BeautifulSoup
import json
import pyperclip


import quiz_create.generators.prompts as prompts
import quiz_create.generators.local_llm as local_llm


class Question:
    pass
    # Question text
    # Answer 
    # Justification span
    # Difficulty

class MCQQuestion(Question):
    pass
    # Distractors

class ClozeQuestion(Question):
    pass
class TFQuestion(Question):
    pass
class ShortAnswerQuestion(Question):
    pass


class Quiz:
    pass

    # Questions
    # Input File
    # from_quiz_data_dict
    # as_txt
    # save_txt

    


def create_quiz(file_path: Path) -> Quiz:
    
    with open(file_path, "r", encoding="utf-8") as f:
        email_data = json.load(f)

    source_text = email_data['email_content']

    prompt = prompts.DEFAULT_PROMPT.format(source=source_text, n=5)

    # Call the generator with the prompt to get questions
    quiz_data = local_llm.create_quiz_data(source_text, prompt)

    # Process the quiz_data to create Quiz and Question objects
    quiz = Quiz.from_quiz_data_dict(quiz_data, file_path)

    # For now, just print the prompt
    print(prompt)
    pyperclip.copy(prompt)
    print("Prompt copied to clipboard.")

    # Return a Quiz object (placeholder for now)
    return quiz


if __name__ == "__main__":
    test_file = constants.CLEANED_EMAIL_DATA_DIR / "Morning_Brew__2025-10-16___In_a_jam__199ec791b7c1dd7b.json"

    quiz = create_quiz(test_file)
    # Save Quiz
    quiz.save_txt()