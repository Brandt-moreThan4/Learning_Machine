import json
import ollama
import time
import logging



MOCK_QUIZ_DATA = {
    "questions": [
        {
            "kind": "mcq",
            "question": "What is the main topic discussed in the email?",
            "answer": "Financial markets",
            "distractors": ["Technology", "Sports", "Politics"],
            "difficulty": "easy",
            "justification_span": "The email discusses various aspects of financial markets and economic trends."
        },
        {
            "kind": "tf",
            "question": "The email mentions specific stock prices.",
            "answer": "True",
            "distractors": [],
            "difficulty": "medium",
            "justification_span": "Stock prices are referenced throughout the document."
        },
        {
            "kind": "short",
            "question": "What are the key takeaways from this email?",
            "answer": "Market volatility and investment strategies",
            "distractors": [],
            "difficulty": "hard",
            "justification_span": "The conclusion summarizes key market insights and strategic recommendations."
        }
    ]
}

def create_quiz_data(prompt: str) -> dict:
    """

    """
    logging.info("Generating quiz data using local LLM...")
    response = ollama.generate(
        model='llama3.1',
        prompt=prompt
    )
    quiz_data_str = response['response']
    try:
        quiz_data = json.loads(quiz_data_str)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse quiz data from LLM response. Response was:\n\n {quiz_data_str}")
        quiz_data = None
    return quiz_data






if __name__ == "__main__":
    prompt = "Tell me the nights watch oath and explain any historical parallels it might have."


    start_time = time.time()
    response = ollama.generate(
        model='llama3.1',
        prompt=prompt
    )
    end_time = time.time()
    
    print(f"Generation took {end_time - start_time:.2f} seconds")
    print(response['response'])
    print('Done!')