"""
Email ingestion module for downloading and cleaning emails from Google Drive.
"""

import os
import io
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .config import Config


class GoogleDriveReader:
    """Class to handle Google Drive operations and email reading."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, config: Config):
        """Initialize the Google Drive reader."""
        self.config = config
        self.service_account_file = Path(config.google_drive.service_account_file)
        self.service = None
        self.creds = None
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API using service account."""
        try:
            if not self.service_account_file.exists():
                self.logger.error(f"Service account file not found: {self.service_account_file}")
                return False
            
            self.creds = service_account.Credentials.from_service_account_file(
                str(self.service_account_file), scopes=self.SCOPES)
            
            self.service = build('drive', 'v3', credentials=self.creds)
            self.logger.info("Successfully authenticated with Google Drive")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def search_files(self, query: str, max_results: int = 100) -> List[Dict]:
        """Search for files in Google Drive."""
        if not self.service:
            self.logger.error("Not authenticated")
            return []
        
        try:
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            self.logger.info(f"Found {len(files)} files matching query")
            return files
            
        except Exception as e:
            self.logger.error(f"Error searching files: {str(e)}")
            return []
    
    def download_file_content(self, file_id: str) -> Optional[str]:
        """Download and return the content of a file."""
        if not self.service:
            self.logger.error("Not authenticated")
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
            self.logger.error(f"Error downloading file {file_id}: {str(e)}")
            return None
    
    def get_html_files(self, folder_id: Optional[str] = None, max_files: int = 50) -> List[Dict]:
        """Get all HTML files from Google Drive."""
        query = "mimeType='text/html'"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        files = self.search_files(query, max_files)
        html_files = []
        
        for file_info in files:
            self.logger.info(f"Downloading: {file_info['name']}")
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


class EmailCleaner:
    """Class to handle email cleaning operations."""
    
    def __init__(self, config: Config):
        """Initialize the email cleaner."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def clean_html_content(self, html_content: str) -> Dict[str, Any]:
        """Clean HTML content and extract text using Beautiful Soup."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract metadata
            title = self._extract_title(soup)
            subject = self._extract_subject(soup)
            sender = self._extract_sender(soup)
            date_info = self._extract_date(soup)
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            cleaned_text = self._clean_text(text_content)
            
            # Extract links
            links = self._extract_links(soup)
            
            return {
                'title': title,
                'subject': subject,
                'sender': sender,
                'date': date_info,
                'text_content': cleaned_text,
                'links': links,
                'word_count': len(cleaned_text.split()),
                'char_count': len(cleaned_text)
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning HTML content: {str(e)}")
            return {
                'title': "Error processing",
                'subject': "Error",
                'sender': "Unknown",
                'date': "Unknown",
                'text_content': f"Error processing file: {str(e)}",
                'links': [],
                'word_count': 0,
                'char_count': 0
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from email."""
        title = soup.find('title')
        return title.get_text().strip() if title else "No title"
    
    def _extract_subject(self, soup: BeautifulSoup) -> str:
        """Extract subject from email."""
        selectors = [
            'meta[name="subject"]', 'meta[name="Subject"]',
            'input[name="subject"]', 'input[name="Subject"]',
            '.subject', '#subject', 'h1', 'h2'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return "No subject found"
    
    def _extract_sender(self, soup: BeautifulSoup) -> str:
        """Extract sender information."""
        selectors = [
            'meta[name="from"]', 'meta[name="From"]',
            'input[name="from"]', 'input[name="From"]',
            '.sender', '.from', '#sender', '#from'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return "Unknown sender"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract date information."""
        selectors = [
            'meta[name="date"]', 'meta[name="Date"]',
            'input[name="date"]', 'input[name="Date"]',
            '.date', '.timestamp', '#date', '#timestamp'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return "Unknown date"
    
    def _extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all links from the email."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith(('http', 'mailto')):
                links.append(href)
        return links
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common email artifacts
        text = re.sub(r'^\s*On\s+.*?wrote:', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*From:\s*.*?$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*To:\s*.*?$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*Subject:\s*.*?$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*Date:\s*.*?$', '', text, flags=re.MULTILINE)
        
        # Remove quoted text (lines starting with >)
        text = re.sub(r'^\s*>.*?$', '', text, flags=re.MULTILINE)
        
        # Remove email headers
        text = re.sub(r'^\s*[A-Za-z-]+:\s*.*?$', '', text, flags=re.MULTILINE)
        
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def save_cleaned_email(self, original_file: Path, cleaned_data: Dict[str, Any]) -> Path:
        """Save cleaned email to output folder."""
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', original_file.stem)
        output_file = Path(self.config.data.cleaned_emails_dir) / f"{safe_name}_cleaned.txt"
        
        content = f"""CLEANED EMAIL
================

Title: {cleaned_data['title']}
Subject: {cleaned_data['subject']}
Sender: {cleaned_data['sender']}
Date: {cleaned_data['date']}
Word Count: {cleaned_data['word_count']}
Character Count: {cleaned_data['char_count']}

LINKS FOUND:
{chr(10).join(f"- {link}" for link in cleaned_data['links']) if cleaned_data['links'] else "No links found"}

CLEANED TEXT:
{chr(10) * 2}{cleaned_data['text_content']}
"""
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Saved cleaned email: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error saving file {output_file}: {str(e)}")
            return None


class EmailIngester:
    """Main class for ingesting emails from Google Drive."""
    
    def __init__(self, config: Config):
        """Initialize the email ingester."""
        self.config = config
        self.drive_reader = GoogleDriveReader(config)
        self.cleaner = EmailCleaner(config)
        self.logger = logging.getLogger(__name__)
    
    def ingest_emails(self, folder_id: Optional[str] = None, max_files: int = 50) -> List[Dict[str, Any]]:
        """Ingest emails from Google Drive and clean them."""
        self.logger.info("Starting email ingestion process...")
        
        # Authenticate with Google Drive
        if not self.drive_reader.authenticate():
            self.logger.error("Failed to authenticate with Google Drive")
            return []
        
        # Get HTML files from Drive
        html_files = self.drive_reader.get_html_files(folder_id, max_files)
        
        if not html_files:
            self.logger.warning("No HTML files found")
            return []
        
        # Process each file
        results = []
        for file_data in html_files:
            self.logger.info(f"Processing: {file_data['name']}")
            
            # Clean the content
            cleaned_data = self.cleaner.clean_html_content(file_data['content'])
            
            # Save cleaned file
            original_file = Path(file_data['name'])
            saved_path = self.cleaner.save_cleaned_email(original_file, cleaned_data)
            
            result = {
                'original_file': file_data['name'],
                'cleaned_file': str(saved_path) if saved_path else None,
                'title': cleaned_data['title'],
                'subject': cleaned_data['subject'],
                'sender': cleaned_data['sender'],
                'word_count': cleaned_data['word_count'],
                'char_count': cleaned_data['char_count'],
                'links_count': len(cleaned_data['links']),
                'success': saved_path is not None
            }
            
            results.append(result)
        
        # Log summary
        successful = sum(1 for r in results if r['success'])
        self.logger.info(f"Ingestion complete: {successful}/{len(results)} files processed successfully")
        
        return results
