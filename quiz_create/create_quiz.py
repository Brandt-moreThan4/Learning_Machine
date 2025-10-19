import constants
from pathlib import Path
import json
from typing import Optional, Union, List

from quiz_create.models import Quiz
from quiz_create.generators import LocalLLMGenerator, OpenAIGenerator
from quiz_create.generators import prompts
from logging_config import default_logger



def create_quiz(
    file_path: Path, 
    generator_type: str = "local_llm",
    generator: Optional[Union[LocalLLMGenerator, OpenAIGenerator]] = None
) -> Quiz:
    """
    Create a quiz from an email file.
    
    Args:
        file_path: Path to the cleaned email JSON file
        generator_type: Type of generator to use ("local_llm" or "openai")
        generator: Optional pre-configured generator instance
        
    Returns:
        Quiz object containing the generated questions
    """
    with open(file_path, "r", encoding="utf-8") as f:
        email_data = json.load(f)

    source_text = email_data['email_content']
    prompt = prompts.DEFAULT_PROMPT.format(source=source_text, n=5)

    # Use provided generator or create one based on type
    if generator is None:
        if generator_type == "local_llm":
            generator = LocalLLMGenerator()
        elif generator_type == "openai":
            generator = OpenAIGenerator()
        else:
            raise ValueError(f"Unknown generator type: {generator_type}")

    # Call the generator with the prompt to get questions
    quiz_data = generator.create_quiz_data(prompt)

    # Process the quiz_data to create Quiz and Question objects
    if quiz_data is not None:
        quiz = Quiz.from_quiz_data_dict(quiz_data, file_path)
    else:
        quiz = Quiz([], file_path)  # Return empty quiz on failure
    return quiz


def create_quizzes_from_files(
    file_paths: List[Path], 
    generator_type: str = "local_llm",
    generator: Optional[Union[LocalLLMGenerator, OpenAIGenerator]] = None
) -> List[Quiz]:
    """
    Create quizzes from a list of file paths.
    
    Args:
        file_paths: List of file paths to create quizzes from
        generator_type: Type of generator to use ("local_llm" or "openai")
        generator: Optional pre-configured generator instance
        
    Returns:
        List of Quiz objects
    """
    return [create_quiz(file_path, generator_type, generator) for file_path in file_paths]

def create_and_save_quizzes(
    file_paths: List[Path], 
    generator_type: str = "local_llm",
    generator: Optional[Union[LocalLLMGenerator, OpenAIGenerator]] = None
) -> List[Quiz]:
    """
    Create and save quizzes from a list of file paths.
    
    Args:
        file_paths: List of file paths to create quizzes from
        generator_type: Type of generator to use ("local_llm" or "openai")
        generator: Optional pre-configured generator instance
        
    Returns:
        List of Quiz objects
    """
    return [create_quiz(file_path, generator_type, generator).save() for file_path in file_paths]


def create_and_save_quizzes_from_directory(
    directory_path: Path, 
    max_quizzes: int = 5,
    generator_type: str = "local_llm",
    generator: Optional[Union[LocalLLMGenerator, OpenAIGenerator]] = None
) -> List[Quiz]:
    """
    Create and save quizzes from a directory of files.
    
    Args:
        directory_path: Path to the directory to create quizzes from
        max_quizzes: Maximum number of quizzes to create
        generator_type: Type of generator to use ("local_llm" or "openai")
        generator: Optional pre-configured generator instance
        
    Returns:
        List of Quiz objects
    """
    quizzes = []
    for file_path in directory_path.glob("*.json"):
        quiz = create_quiz(file_path, generator_type, generator)
        quizzes.append(quiz)
        if len(quizzes) >= max_quizzes:
            break
    for quiz in quizzes:
        quiz.save()
    return quizzes


if __name__ == "__main__":
    test_file = constants.CLEANED_EMAIL_DATA_DIR / "Morning_Brew__2025-10-16___In_a_jam__199ec791b7c1dd7b.json"

    quiz = create_quiz(test_file, generator_type="openai")
    # Save quiz to file (defaults to HTML)
    if quiz is not None:
        quiz.save()
    
    # quizzes = create_and_save_quizzes_from_directory(constants.CLEANED_EMAIL_DATA_DIR, 
    #     max_quizzes=5,
    #  generator_type="openai")

    default_logger.info('Done')