# email_quizzer/generators/local_llm.py
import json, subprocess


PROMPT = """You are generating quiz questions strictly from SOURCE.
Return a JSON list of objects with fields:
kind (mcq|cloze|tf|short), question, answer, distractors(3 for mcq else []),
difficulty (easy|medium|hard), justification_span (<=200 chars from SOURCE).
SOURCE:
<<<
{source}
>>>
Write {n} questions.
"""

def _run_ollama(prompt: str, model: str = "mistral:instruct") -> str:
    # Requires `ollama serve` running locally
    p = subprocess.run(["ollama", "run", model], input=prompt.encode(), capture_output=True)
    return p.stdout.decode("utf-8")

def generate(source: str, n: int) -> list[QuizItem]:
    raw = _run_ollama(PROMPT.format(source=source, n=n))
    try:
        data = json.loads(raw)
        items = [QuizItem(**d) for d in data if isinstance(d, dict)]
        return items
    except Exception:
        return []
