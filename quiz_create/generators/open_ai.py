import os, logging
from typing import Literal, List
from pydantic import BaseModel
from openai import OpenAI

CHOSEN_OPEN_AI_MODEL = "gpt-4o-mini"  # must support Responses + structured outputs

class Question(BaseModel):
    kind: Literal["mcq","cloze","tf","short"]
    question: str
    answer: str
    distractors: List[str]  # [] for non-MCQ
    difficulty: Literal["easy","medium","hard"]
    answer_justification: str

class QuizData(BaseModel):
    questions: List[Question]

TOY_PROMPT = """You are generating a quiz.

Return a JSON object with a single key "questions" whose value is a list of objects with fields:
 - kind (mcq|cloze|tf|short)
 - question
 - answer
 - distractors (3 for mcq, otherwise an empty list)
 - difficulty (easy|medium|hard)
 - answer_justification (<=200 chars)

Content: the Night's Watch from A Song of Ice and Fire.
Write exactly 3 questions.
Output only JSON for that object.
"""

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)

client = get_openai_client()

def create_quiz_data(prompt: str) -> QuizData:
    logging.info("Generating quiz data using OpenAI LLM (Responses API)...")
    resp = client.responses.parse(
        model=CHOSEN_OPEN_AI_MODEL,
        input=prompt,                 # <-- string, not messages
        text_format=QuizData,         # <-- Pydantic schema
    )
    return resp.output_parsed        # <-- a QuizData instance

if __name__ == "__main__":
    quiz = create_quiz_data(TOY_PROMPT)
    print(quiz.model_dump_json(indent=2))
