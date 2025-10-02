"""
Google Drive HTML File Reader

This script connects to Google Drive API to read HTML files for processing.
Requires proper authentication setup with Google Drive API.
"""

import os
import io
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import re


class GoogleDriveReader:
    """Class to handle Google Drive operations and HTML file reading."""
    
    # Scopes required for Google Drive access
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, service_account_file: str = 'service_account.json'):
        """
        Initialize the Google Drive reader.
        
        Args:
            service_account_file: Path to Google service account JSON file
        """
        self.service_account_file = service_account_file
        self.service = None
        self.creds = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API using service account.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not os.path.exists(self.service_account_file):
                print(f"Error: {self.service_account_file} not found!")
                print("Please download your service account key from Google Cloud Console.")
                return False
            
            # Create credentials from service account file
            self.creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES)
            
            # Build the service
            self.service = build('drive', 'v3', credentials=self.creds)
            print("Successfully authenticated with Google Drive using service account!")
            return True
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return False
    
    def search_files(self, query: str = "mimeType='text/html'", max_results: int = 100) -> List[Dict]:
        """
        Search for files in Google Drive.
        
        Args:
            query: Search query (default finds HTML files)
            max_results: Maximum number of results to return
            
        Returns:
            List of file metadata dictionaries
        """
        if not self.service:
            print("Not authenticated. Please call authenticate() first.")
            return []
        
        try:
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            print(f"Found {len(files)} files matching query: {query}")
            return files
            
        except Exception as e:
            print(f"Error searching files: {str(e)}")
            return []
    
    def download_file_content(self, file_id: str) -> Optional[str]:
        """
        Download and return the content of a file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File content as string, or None if error
        """
        if not self.service:
            print("Not authenticated. Please call authenticate() first.")
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            content = file_content.getvalue().decode('utf-8')
            return content
            
        except Exception as e:
            print(f"Error downloading file {file_id}: {str(e)}")
            return None
    
    def get_html_files(self, folder_id: Optional[str] = None, max_files: int = 50) -> List[Dict]:
        """
        Get all HTML files from Google Drive.
        
        Args:
            folder_id: Specific folder ID to search in (optional)
            max_files: Maximum number of files to retrieve
            
        Returns:
            List of dictionaries containing file info and content
        """
        # Build query for HTML files
        query = "mimeType='text/html'"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        files = self.search_files(query, max_files)
        html_files = []
        
        for file_info in files:
            print(f"Downloading: {file_info['name']}")
            content = self.download_file_content(file_info['id'])
            
            if content:
                html_files.append({
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'size': file_info.get('size', 'Unknown'),
                    'modified': file_info.get('modifiedTime', 'Unknown'),
                    'content': content
                })
        
        return html_files
    
    def process_html_content(self, html_content: str) -> Dict:
        """
        Process HTML content to extract useful information.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dictionary with processed information
        """
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No title found"
        
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', 
                              html_content, re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else "No description found"
        
        # Count various HTML elements
        link_count = len(re.findall(r'<a[^>]*>', html_content, re.IGNORECASE))
        img_count = len(re.findall(r'<img[^>]*>', html_content, re.IGNORECASE))
        div_count = len(re.findall(r'<div[^>]*>', html_content, re.IGNORECASE))
        
        # Extract text content (basic)
        text_content = re.sub(r'<[^>]+>', '', html_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return {
            'title': title,
            'description': description,
            'link_count': link_count,
            'image_count': img_count,
            'div_count': div_count,
            'text_length': len(text_content),
            'preview_text': text_content[:200] + "..." if len(text_content) > 200 else text_content
        }


def main():
    """Main function to demonstrate usage."""
    print("Google Drive HTML File Reader")
    print("=" * 40)
    
    # Initialize the reader
    reader = GoogleDriveReader()
    
    # Authenticate
    if not reader.authenticate():
        print("Failed to authenticate. Please check your credentials.")
        return
    
    # Get HTML files
    print("\nSearching for HTML files...")
    html_files = reader.get_html_files(max_files=10)  # Limit to 10 for demo
    
    if not html_files:
        print("No HTML files found.")
        return
    
    print(f"\nFound {len(html_files)} HTML files:")
    print("-" * 50)
    
    # Process each file
    for i, file_data in enumerate(html_files, 1):
        print(f"\n{i}. {file_data['name']}")
        print(f"   Size: {file_data['size']} bytes")
        print(f"   Modified: {file_data['modified']}")
        
        # Process the HTML content
        processed = reader.process_html_content(file_data['content'])
        print(f"   Title: {processed['title']}")
        print(f"   Description: {processed['description']}")
        print(f"   Links: {processed['link_count']}, Images: {processed['image_count']}")
        print(f"   Text length: {processed['text_length']} characters")
        print(f"   Preview: {processed['preview_text']}")
    
    print(f"\nProcessing complete! Found {len(html_files)} HTML files.")


if __name__ == "__main__":
    main()
