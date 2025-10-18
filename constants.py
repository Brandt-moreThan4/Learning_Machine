from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
EMAIL_DOWNLOAD_DIR = PROJECT_ROOT / "Email_Download"

DATA_DIR = PROJECT_ROOT / "data"
RAW_EMAIL_DATA_DIR = DATA_DIR / "raw_emails"
CLEANED_EMAIL_DATA_DIR = DATA_DIR / "cleaned_emails"
QUIZ_OUTPUT_DIR = DATA_DIR / "quizzes"
