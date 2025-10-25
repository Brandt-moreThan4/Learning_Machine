from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).parent
EMAIL_DOWNLOAD_DIR = PROJECT_ROOT / "email_download"

DATA_DIR = PROJECT_ROOT / "data"
RAW_EMAIL_DATA_DIR = DATA_DIR / "raw_emails"
CLEANED_EMAIL_DATA_DIR = DATA_DIR / "cleaned_emails"

QUIZ_OUTPUT_DIR = DATA_DIR / "quizzes"
QUIZ_HTML_DIR = QUIZ_OUTPUT_DIR / "quiz_html"
QUIZ_JSON_DIR = QUIZ_OUTPUT_DIR / "quiz_json"

load_dotenv()
