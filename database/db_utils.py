from database.db_connect import create_db_connection
from sqlalchemy import create_engine, text
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

def db_connection_works() -> bool:
    """Test the database connection by executing a simple query."""

    bg_engine = create_db_connection()

    query = f""" select *  from quiz_app.quizzes limit 1;"""
    try:
        with bg_engine.connect() as connection:
            result = connection.execute(text(query))
            # Fetch one row to ensure query executed successfully
            row = result.fetchone()
            return True
    except Exception as e:
        print("Database connection test failed:", e)
        return False


if __name__ == "__main__":
    ids = get_quiz_ids_from_db()
    print(ids)