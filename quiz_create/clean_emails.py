import constants
from pathlib import Path
from bs4 import BeautifulSoup


# To Do
# Save as json with metadata
# Add word counts
# Strip out footers?
# Store only unique id as file name?


def clean_emails():

    # Loop through all the files in the raw_emails directory
    for raw_email_file in constants.RAW_EMAIL_DATA_DIR.glob("*"):
        # Read the file with UTF-8 encoding to handle special characters
        with open(raw_email_file, "r", encoding="utf-8", errors="replace") as f:
            raw_html = f.read()
        # Clean the html
        soup = BeautifulSoup(raw_html, "html.parser")

        cleaned_text = soup.get_text()
        new_file_name = raw_email_file.name.replace(".html", ".txt")
        with open(constants.CLEANED_EMAIL_DATA_DIR / new_file_name, "w", encoding="utf-8") as f:
            f.write(cleaned_text)




if __name__ == "__main__":
    clean_emails()