import constants
from pathlib import Path
import json
from typing import Optional, Union

from quiz_create.models import Quiz
from quiz_create.generators import LocalLLMGenerator, OpenAIGenerator
from quiz_create.generators import prompts


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


if __name__ == "__main__":
    test_file = constants.CLEANED_EMAIL_DATA_DIR / "Morning_Brew__2025-10-16___In_a_jam__199ec791b7c1dd7b.json"

    # Example using local LLM (default)
    quiz = create_quiz(test_file, generator_type="openai")
    
    # Example using OpenAI
    # quiz = create_quiz(test_file, generator_type="openai")
    
    # Example using custom generator
    # custom_generator = LocalLLMGenerator(model="llama3.1")
    # quiz = create_quiz(test_file, generator=custom_generator)
    
    # Display quiz content
    print("Generated Quiz:")
    
    # Save quiz to file (defaults to HTML)
    if quiz is not None:
        quiz.save()
    
    # Example of saving in different formats:
    # quiz.save("markdown")  # Save as markdown
    # quiz.save("txt")      # Save as text
    # quiz.save("html")     # Save as HTML (default)
    print('Done')