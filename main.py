import email_download.email_download as ed
from quiz_create import clean_emails as ce
import utils
from utils import default_logger
from quiz_create import create_quiz
import email_sender
from database import db_utils

# Set up logging
utils.setup_logging()

utils.create_necessary_dirs()

def main():
    default_logger.info("Starting Learning Machine pipeline...")

    # Download new emails
    default_logger.info("Downloading new emails...")
    downloader = ed.EmailDownloader()
    downloader.download_files(max_files=30)

    # Clean downloaded emails
    default_logger.info("Cleaning downloaded emails...")
    ce.clean_emails()

    # Create quizzes from cleaned emails (Also saves to DB)
    default_logger.info("Creating quizzes from cleaned emails...")
    create_quiz.create_new_quizzes(max_quiz_count=10)

    # Email quizzes

    if db_utils.db_connection_works():
        default_logger.info("Sending new quiz emails...")
        email_sender.send_new_quiz_emails()
    else:
        default_logger.error("Database connection failed. Skipping email sending.")

    default_logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()

