import constants
from pathlib import Path


def delete_files_in_directory(directory: Path):
    for file in directory.glob("*"):
        file.unlink()



if __name__ == "__main__":
    delete_files_in_directory(constants.RAW_EMAIL_DATA_DIR)