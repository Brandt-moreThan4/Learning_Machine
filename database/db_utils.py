from database.db_connect import create_db_connection
import pandas as pd
from typing import List


def get_quiz_ids_from_db() -> List[str]:
    """
    Retrieve all quiz IDs from the database.
    
    Returns:
        List[str]: List of quiz IDs
    """
    engine = create_db_connection()
    
    query = f""" select distinct id from quiz_app.quizzes; """
    quiz_ids = pd.read_sql(query, engine)
    quiz_ids = quiz_ids['id'].tolist()
    return quiz_ids


if __name__ == "__main__":
    ids = get_quiz_ids_from_db()
    print(ids)