
import logging
import json
import time
from openai import OpenAI
import os
from pydantic import BaseModel
import prompts

CHOSEN_OPEN_AI_MODEL = "gpt-4o-mini"


TOY_PROMPT = """You are generating a quiz.
Return a JSON list of objects with fields:
 - kind (mcq|cloze|tf|short)
 - question
 - answer
 - distractors(3 for mcq else [])
 - difficulty (easy|medium|hard)
 - answer_justification (<=200).

<<<
The quiz content should be about the nights watch from A Song of Ice and Fire.
>>>
Write 3 questions.
Return only the Json list. 
"""



class Question(BaseModel):
    question: str
    answer: str
    answer_justification: str
    difficulty: str
    distractors: list # Can be empty for non-MCQ questions

class QuizData(BaseModel):
    questions: list[Question]



def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    return client

client = get_openai_client()

def print_available_models():
    client = get_openai_client()
    models = client.models.list()
    for model in models.data:
        print(model.id)


def create_quiz_data_json(prompt:str) -> dict:
    """
    Create quiz data using OpenAI's API.
    
    Args:
        prompt: The prompt to send to the LLM.
        
    Returns:
        Parsed JSON quiz data.
    """
    logging.info("Generating quiz data using OpenAI LLM...")
    response = client.chat.completions.create(
        model=CHOSEN_OPEN_AI_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
    )
    quiz_data = response.choices[0].message.content

    try:
        quiz_data = json.loads(quiz_data)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse quiz data from LLM response. Response was:\n\n {quiz_data}")
        quiz_data = {}

    return quiz_data


def create_quiz_data(prompt:str) -> dict:
    """
    Create quiz data using OpenAI's API.
    
    Args:
        prompt: The prompt to send to the LLM.
        
    Returns:
        Parsed JSON quiz data.
    """
    logging.info("Generating quiz data using OpenAI LLM...")
    response = client.responses.parse(
        model=CHOSEN_OPEN_AI_MODEL,
        input=[
            {"role": "user", "content": prompt}
        ],
        text_format=QuizData,
    )

    quiz_data = response.output_parsed
    return quiz_data


if __name__ == "__main__":
    # prompt = "Tell me the nights watch oath and explain any historical parallels it might have."
    prompt = "Generate a quiz with 5 questions about the history of the Roman Empire. Include multiple choice, true/false, and short answer questions. Provide answers and explanations for each question."

    # print_available_models()
    response_format={"type": "json_object"},
    start_time = time.time()
    # response = client.chat.completions.create(
    #     model=CHOSEN_OPEN_AI_MODEL,
    #     messages=[
    #         {"role": "user", "content": prompts.TOY_PROMPT}
    #     ],
    #     response_format={"type": "json_object"},
    # )

    quiz = create_quiz_data(TOY_PROMPT)

    print('Done!')

