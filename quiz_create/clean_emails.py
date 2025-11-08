import constants
from pathlib import Path
from bs4 import BeautifulSoup
import json


# To Do
# Strip out footers?
# Only clean latest emails... Honestly, it's fine for now to clean everything. It's pretty quick. 

def clean_emails():

    # Loop through all the files in the raw_emails directory
    for raw_email_file in constants.RAW_EMAIL_DATA_DIR.glob("*"):

        # Read the file with UTF-8 encoding to handle special characters
        with open(raw_email_file, "r", encoding="utf-8", errors="replace") as f:
            raw_html = f.read()

        # Clean the html
        soup = BeautifulSoup(raw_html, "html.parser")
        cleaned_text = soup.get_text()

        # Collect some metadata based on file name. 
        # Example file name: Money_Stuff_2025-10-06_Money_Stuff_OpenAI_Is_Good_at_Deals_199ba92360bedc3e.html
        file_meta_data = raw_email_file.stem.split("__")
        data = {}
        data['sender'] = file_meta_data[0]
        data['date'] = file_meta_data[1]
        data['subject'] = file_meta_data[2]
        data['word'] = len(cleaned_text.split())
        data['email_content'] = cleaned_text

        new_file_path = raw_email_file.name.replace(".html", ".json")

        with open(constants.CLEANED_EMAIL_DATA_DIR / new_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    clean_emails()