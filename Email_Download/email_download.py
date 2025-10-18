"""
Simple Google Drive Email Downloader

Downloads HTML files from Google Drive and saves them with original filenames.
"""

import os
import io
import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

sys.path.append(str(Path(__file__).parent.parent))
import constants


class EmailDownloader:
    """Simple email downloader that reads and saves files with original names."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, service_account_file='service_account.json'):
        """Initialize with service account file."""
        self.service_account_file = Path(__file__).parent / service_account_file
        self.output_folder = constants.RAW_EMAIL_DATA_DIR
        self.service = None
        
        # Create output folder if it doesn't exist
        self.output_folder.mkdir(exist_ok=True)

        # Autho-authenticate on initialization
        self.authenticate() 
    
    def authenticate(self):
        """Authenticate with Google Drive API."""
        try:
            if not os.path.exists(self.service_account_file):
                print(f"Error: {self.service_account_file} not found!")
                return False
            
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            print("Successfully authenticated!")
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise e
    
    def download_files(self, max_files=50):
        """Download HTML files and save with original names."""
        if not self.service:
            print("Not authenticated!")
            return
        
        # Search for HTML files
        results = self.service.files().list(
            q="mimeType='text/html'",
            pageSize=max_files,
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        print(f"Found {len(files)} HTML files")
        
        for file_info in files:
            file_name = file_info['name']
            file_id = file_info['id']
            
            print(f"Downloading: {file_name}")
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            content = file_content.getvalue().decode('utf-8')
            
            # Save with sanitized filename (Windows doesn't allow certain characters)
            safe_filename = file_name.replace('|', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_')
            file_path = self.output_folder / safe_filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Saved: {file_path}")


def main():
    """Main function to download emails."""
    print("Email Downloader")
    print("=" * 20)
    
    downloader = EmailDownloader()
    
    if not downloader.authenticate():
        print("Failed to authenticate!")
        return
    
    downloader.download_files(max_files=20)
    print(f"\nFiles saved to: {downloader.output_folder}")


if __name__ == "__main__":
    main()