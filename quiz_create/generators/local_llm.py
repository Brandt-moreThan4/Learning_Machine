import json


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

def create_quiz_data(input_text: str, prompt: str) -> dict:
    """
    Create quiz data from input text using the provided prompt.
    This is a placeholder implementation that returns mock data.
    In a real implementation, this would call a local LLM.
    """
    # Mock implementation - replace with actual LLM call

        
    return MOCK_QUIZ_DATA