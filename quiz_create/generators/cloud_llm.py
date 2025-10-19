
import logging
import json
from time import time
from openai import OpenAI

# def create_quiz_data(prompt: str) -> dict:
#     """

#     """
#     logging.info("Generating quiz data using local LLM...")


#     quiz_data_str = response['response']
#     try:
#         quiz_data = json.loads(quiz_data_str)
#     except json.JSONDecodeError:
#         logging.error(f"Failed to parse quiz data from LLM response. Response was:\n\n {quiz_data_str}")
#         quiz_data = None
#     return quiz_data




if __name__ == "__main__":
    prompt = "Tell me the nights watch oath and explain any historical parallels it might have."


    start_time = time.time()
    client = OpenAI()
    print(client.models.list().data[0].id)
    end_time = time.time()
    print(f"Generation took {end_time - start_time:.2f} seconds")
    # print(response['response'])
    print('Done!')

