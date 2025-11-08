"""
Simple Google Drive Email Downloader

Downloads HTML files from Google Drive and saves them with original filenames.
"""

import os
import io
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

sys.path.append(str(Path(__file__).parent.parent))
import constants
from utils import default_logger, setup_logging

# Initialize logging
setup_logging()


class EmailDownloader:
    """Simple email downloader that reads and saves files with original names."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, service_account_file='service_account.json', days_back=7):
        """Initialize with service account file."""
        self.service_account_file = Path(__file__).parent / service_account_file
        self.output_folder = constants.RAW_EMAIL_DATA_DIR
        self.service = None
        self.days_back = days_back
        
        # Create output folder if it doesn't exist
        self.output_folder.mkdir(exist_ok=True)

        # Autho-authenticate on initialization
        self.authenticate() 
    
    def authenticate(self):
        """Authenticate with Google Drive API."""
        try:
            if not os.path.exists(self.service_account_file):
                default_logger.error(f"Error: {self.service_account_file} not found!")
                return False
            
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            default_logger.info("Successfully authenticated!")
            return True
        except Exception as e:
            default_logger.error(f"Authentication failed: {e}")
            raise e
    
    def get_existing_filenames(self):
        """Get set of existing filenames to check for duplicates."""
        existing_files = set()
        if self.output_folder.exists():
            for file_path in self.output_folder.iterdir():
                if file_path.is_file() and file_path.suffix == '.html':
                    existing_files.add(file_path.name)
        default_logger.info(f"Found {len(existing_files)} existing files")
        return existing_files
    
    def download_files(self, max_files=50):
        """Download HTML files and save with original names, checking for newer emails first."""
        if not self.service:
            default_logger.error("Not authenticated!")
            return
        
        # Get existing filenames
        existing_files = self.get_existing_filenames()
        
        # Calculate date threshold for newer emails
        date_threshold = datetime.now() - timedelta(days=self.days_back)
        default_logger.info(f"Looking for emails newer than: {date_threshold}")
        
        # Build query for HTML files with date filter
        date_str = date_threshold.strftime('%Y-%m-%dT%H:%M:%S')
        query = f"mimeType='text/html' and modifiedTime>'{date_str}'"
        
        # Search for HTML files newer than threshold
        results = self.service.files().list(
            q=query,
            pageSize=max_files,
            orderBy='modifiedTime desc',  # Newest first
            fields="files(id, name, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        default_logger.info(f"Found {len(files)} HTML files newer than threshold")
        
        if len(files) == 0:
            default_logger.info("No new files found. This could mean:")
            default_logger.info("1. No emails were modified in the last 7 days")
            default_logger.info("2. The Google Drive folder is empty")
            default_logger.info("3. The API query didn't match any files")
        
        downloaded_count = 0
        skipped_count = 0
        
        for file_info in files:
            file_name = file_info['name']
            file_id = file_info['id']
            
            # Create safe filename
            safe_filename = file_name.replace('|', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_')
            
            # Check if file already exists by filename
            if safe_filename in existing_files:
                default_logger.info(f"Skipping existing file: {safe_filename}")
                skipped_count += 1
                continue
            
            default_logger.info(f"Downloading: {file_name}")
            
            try:
                # Download file content
                request = self.service.files().get_media(fileId=file_id)
                file_content = io.BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                content = file_content.getvalue().decode('utf-8')
                
                # Save file
                file_path = self.output_folder / safe_filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                downloaded_count += 1
                default_logger.info(f"Saved: {file_path}")
                
            except Exception as e:
                default_logger.error(f"Failed to download {file_name}: {e}")
                continue
        
        default_logger.info(f"Download complete: {downloaded_count} new files, {skipped_count} skipped")


def main():
    """Main function to download emails."""
    default_logger.info("Email Downloader (Incremental)")
    default_logger.info("=" * 30)
    
    # Initialize with 7 days back for first run, then incremental
    downloader = EmailDownloader(days_back=7)
    
    if not downloader.authenticate():
        default_logger.error("Failed to authenticate!")
        return
    
    downloader.download_files(max_files=20)
    default_logger.info(f"\nFiles saved to: {downloader.output_folder}")


if __name__ == "__main__":
    main()