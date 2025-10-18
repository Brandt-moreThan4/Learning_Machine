import Email_Download.email_download as ed
from quiz_create import clean_emails as ce
import utils

utils.create_necessary_dirs()

def main():

    # Download new emails
    downloader = ed.EmailDownloader()
    downloader.download_files(max_files=30)

    # Clean downloaded emails
    ce.clean_emails()

if __name__ == "__main__":
    main()

