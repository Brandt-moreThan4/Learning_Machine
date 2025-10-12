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
from pathlib import Path
import datetime


class GoogleDriveReader:
    """Class to handle Google Drive operations and HTML file reading."""
    
    # Scopes required for Google Drive access
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, service_account_file: str = 'service_account.json', output_folder: str = 'output'):
        """
        Initialize the Google Drive reader.
        
        Args:
            service_account_file: Path to Google service account JSON file
            output_folder: Folder to save downloaded HTML files
        """
        parent_dir = Path(__file__).parent
        self.service_account_file = parent_dir / service_account_file
        self.output_folder = parent_dir / output_folder
        self.service = None
        self.creds = None
        
        # Create output folder if it doesn't exist
        self.output_folder.mkdir(exist_ok=True)
        
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
    
    def list_folders(self, parent_folder_id: str = None, max_results: int = 100) -> List[Dict]:
        """
        List all folders accessible to the service account.
        
        Args:
            parent_folder_id: ID of parent folder to search in (None for root)
            max_results: Maximum number of folders to return
            
        Returns:
            List of folder dictionaries with id, name, and path info
        """
        if not self.service:
            print("Not authenticated. Please call authenticate() first.")
            return []
        
        try:
            # Build query for folders
            query = "mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            else:
                query += " and 'root' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, parents, modifiedTime)"
            ).execute()
            
            folders = results.get('files', [])
            print(f"Found {len(folders)} folders")
            return folders
            
        except Exception as e:
            print(f"Error listing folders: {str(e)}")
            return []
    
    def get_folder_path(self, folder_id: str) -> str:
        """
        Get the full path of a folder by its ID.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            Full path string (e.g., "My Drive/Projects/HTML Files")
        """
        if not self.service:
            return "Not authenticated"
        
        try:
            path_parts = []
            current_id = folder_id
            
            while current_id and current_id != 'root':
                file_info = self.service.files().get(
                    fileId=current_id,
                    fields="id, name, parents"
                ).execute()
                
                path_parts.insert(0, file_info['name'])
                parents = file_info.get('parents', [])
                current_id = parents[0] if parents else None
            
            return "/".join(path_parts) if path_parts else "My Drive"
            
        except Exception as e:
            print(f"Error getting folder path: {str(e)}")
            return f"Error: {str(e)}"
    
    def explore_folder_structure(self, max_depth: int = 3, current_folder_id: str = None, current_depth: int = 0) -> None:
        """
        Recursively explore and print folder structure.
        
        Args:
            max_depth: Maximum depth to explore
            current_folder_id: Current folder ID (None for root)
            current_depth: Current depth level
        """
        if current_depth >= max_depth:
            return
        
        # Get folders in current level
        folders = self.list_folders(current_folder_id)
        
        if not folders:
            return
        
        indent = "  " * current_depth
        folder_name = "Root" if current_folder_id is None else self.get_folder_path(current_folder_id)
        
        print(f"{indent}📁 {folder_name}")
        
        for folder in folders:
            folder_id = folder['id']
            folder_name = folder['name']
            print(f"{indent}  📁 {folder_name} (ID: {folder_id})")
            
            # Recursively explore subfolders
            if current_depth < max_depth - 1:
                self.explore_folder_structure(max_depth, folder_id, current_depth + 1)
    
    def search_in_folder(self, folder_id: str, file_type: str = "html", max_files: int = 50) -> List[Dict]:
        """
        Search for specific file types within a folder.
        
        Args:
            folder_id: Google Drive folder ID to search in
            file_type: Type of files to search for ('html', 'pdf', 'doc', etc.)
            max_files: Maximum number of files to return
            
        Returns:
            List of file dictionaries
        """
        if not self.service:
            print("Not authenticated. Please call authenticate() first.")
            return []
        
        try:
            # Build query based on file type
            if file_type.lower() == 'html':
                mime_type = "mimeType='text/html'"
            elif file_type.lower() == 'pdf':
                mime_type = "mimeType='application/pdf'"
            elif file_type.lower() == 'doc':
                mime_type = "mimeType='application/vnd.google-apps.document'"
            else:
                mime_type = f"name contains '.{file_type}'"
            
            query = f"{mime_type} and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_files,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            print(f"Found {len(files)} {file_type} files in folder {folder_id}")
            return files
            
        except Exception as e:
            print(f"Error searching in folder: {str(e)}")
            return []
    
    def save_html_file(self, file_name: str, content: str, file_id: str = None) -> str:
        """
        Save HTML content to a file in the output folder.
        
        Args:
            file_name: Name of the file to save
            content: HTML content to save
            file_id: Google Drive file ID (for unique naming if needed)
            
        Returns:
            Path to the saved file
        """
        # Clean filename to avoid issues
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file_name)
        
        # Add timestamp and file ID to make filename unique if needed
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if file_id:
            name_parts = safe_filename.rsplit('.', 1)
            if len(name_parts) == 2:
                safe_filename = f"{name_parts[0]}_{file_id[:8]}_{timestamp}.{name_parts[1]}"
            else:
                safe_filename = f"{safe_filename}_{file_id[:8]}_{timestamp}.html"
        else:
            # Ensure .html extension
            if not safe_filename.lower().endswith('.html'):
                safe_filename += '.html'
        
        # Create full path
        file_path = self.output_folder / safe_filename
        
        # Save the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Saved: {file_path}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving file {safe_filename}: {str(e)}")
            return None
    
    def get_html_files(self, folder_id: Optional[str] = None, max_files: int = 50, save_files: bool = True) -> List[Dict]:
        """
        Get all HTML files from Google Drive.
        
        Args:
            folder_id: Specific folder ID to search in (optional)
            max_files: Maximum number of files to retrieve
            save_files: Whether to save files to output folder
            
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
                # Save file to output folder if requested
                saved_path = None
                if save_files:
                    saved_path = self.save_html_file(
                        file_info['name'], 
                        content, 
                        file_info['id']
                    )
                
                html_files.append({
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'size': file_info.get('size', 'Unknown'),
                    'modified': file_info.get('modifiedTime', 'Unknown'),
                    'content': content,
                    'saved_path': saved_path
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
    
    # Explore folder structure first
    print("\n📁 Exploring your Drive folder structure...")
    print("=" * 50)
    reader.explore_folder_structure(max_depth=2)
    
    # List top-level folders
    print("\n📁 Top-level folders you have access to:")
    print("-" * 40)
    folders = reader.list_folders()
    for i, folder in enumerate(folders, 1):
        print(f"{i}. {folder['name']} (ID: {folder['id']})")
    
    # Get HTML files and save them to output folder
    print("\n🔍 Searching for HTML files...")
    html_files = reader.get_html_files(max_files=10, save_files=True)  # Limit to 10 for demo
    
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
        if file_data.get('saved_path'):
            print(f"   Saved to: {file_data['saved_path']}")
        
        # Process the HTML content
        processed = reader.process_html_content(file_data['content'])
        print(f"   Title: {processed['title']}")
        print(f"   Description: {processed['description']}")
        print(f"   Links: {processed['link_count']}, Images: {processed['image_count']}")
        print(f"   Text length: {processed['text_length']} characters")
        print(f"   Preview: {processed['preview_text']}")
    
    print(f"\nProcessing complete! Found {len(html_files)} HTML files.")
    print(f"Files saved to: {reader.output_folder}")


if __name__ == "__main__":
    main()
