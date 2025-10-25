from pathlib import Path

import constants



def create_necessary_dirs():
    constants.DATA_DIR.mkdir(exist_ok=True)
    constants.RAW_EMAIL_DATA_DIR.mkdir(exist_ok=True)
    constants.CLEANED_EMAIL_DATA_DIR.mkdir(exist_ok=True)
    constants.QUIZ_OUTPUT_DIR.mkdir(exist_ok=True)
    constants.QUIZ_HTML_DIR.mkdir(exist_ok=True)
    constants.QUIZ_JSON_DIR.mkdir(exist_ok=True)



