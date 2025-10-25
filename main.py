import email_download.email_download as ed
from quiz_create import clean_emails as ce
import utils
from logging_config import setup_logging, default_logger
from quiz_create import create_quiz

# Set up logging
setup_logging()

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

    # Create quizzes from cleaned emails
    default_logger.info("Creating quizzes from cleaned emails...")
    create_quiz.create_new_quizzes(max_quiz_count=3)
    
    default_logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()

