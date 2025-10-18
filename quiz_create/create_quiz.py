import constants
from pathlib import Path
from bs4 import BeautifulSoup
import json
import pyperclip

# import generators
import prompts

# Question types: mcq, cloze, tf, short answer

class Question:
    pass
# Question text
# Answer 


class Quiz:
    pass

    # Questions
    # Input File
    # full output
    




def create_quiz(file_path: Path) -> Quiz:
    
    with open(file_path, "r", encoding="utf-8") as f:
        email_data = json.load(f)

    source_text = email_data['email_content']

    prompt = prompts.DEFAULT_PROMPT.format(source=source_text, n=5)

    # Call the generator with the prompt to get questions
    # questions = generators.generate_questions(prompt)

    # For now, just print the prompt
    print(prompt)
    pyperclip.copy(prompt)
    print("Prompt copied to clipboard.")

    # Return a Quiz object (placeholder for now)
    return Quiz()


if __name__ == "__main__":
    test_file = constants.CLEANED_EMAIL_DATA_DIR / "Morning_Brew__2025-10-16___In_a_jam__199ec791b7c1dd7b.json"

    create_quiz(test_file)