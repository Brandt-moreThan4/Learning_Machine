"""
Email Cleaning Script

This script reads raw email files from Google Drive download,
cleans them using Beautiful Soup to extract text only,
and saves the cleaned files.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime


class EmailCleaner:
    """Class to handle email cleaning operations."""
    
    def __init__(self, input_folder: str = "gdrive_access/output", output_folder: str = "cleaned_emails"):
        """
        Initialize the email cleaner.
        
        Args:
            input_folder: Folder containing raw email files
            output_folder: Folder to save cleaned files
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.cleaned_files = []
        
        # Create output folder if it doesn't exist
        self.output_folder.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for the email cleaner."""
        log_file = self.output_folder / "email_cleaning.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_email_files(self, extensions: List[str] = None) -> List[Path]:
        """
        Find all email files in the input folder.
        
        Args:
            extensions: List of file extensions to look for
            
        Returns:
            List of file paths
        """
        if extensions is None:
            extensions = ['.html', '.htm', '.eml', '.txt']
        
        email_files = []
        
        for ext in extensions:
            pattern = f"**/*{ext}"
            files = list(self.input_folder.glob(pattern))
            email_files.extend(files)
        
        self.logger.info(f"Found {len(email_files)} email files")
        return email_files
    
    def clean_html_content(self, html_content: str) -> Dict[str, str]:
        """
        Clean HTML content and extract text using Beautiful Soup.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dictionary with cleaned content and metadata
        """
        try:
            # Parse HTML with Beautiful Soup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract subject from meta tags or headers
            subject = self.extract_subject(soup)
            
            # Extract sender information
            sender = self.extract_sender(soup)
            
            # Extract date information
            date_info = self.extract_date(soup)
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Clean up the text
            cleaned_text = self.clean_text(text_content)
            
            # Extract links
            links = self.extract_links(soup)
            
            return {
                'title': title_text,
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
    
    def extract_subject(self, soup: BeautifulSoup) -> str:
        """Extract subject from email."""
        # Try different methods to find subject
        subject_selectors = [
            'meta[name="subject"]',
            'meta[name="Subject"]',
            'input[name="subject"]',
            'input[name="Subject"]',
            '.subject',
            '#subject',
            'h1',
            'h2'
        ]
        
        for selector in subject_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return "No subject found"
    
    def extract_sender(self, soup: BeautifulSoup) -> str:
        """Extract sender information."""
        sender_selectors = [
            'meta[name="from"]',
            'meta[name="From"]',
            'input[name="from"]',
            'input[name="From"]',
            '.sender',
            '.from',
            '#sender',
            '#from'
        ]
        
        for selector in sender_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return "Unknown sender"
    
    def extract_date(self, soup: BeautifulSoup) -> str:
        """Extract date information."""
        date_selectors = [
            'meta[name="date"]',
            'meta[name="Date"]',
            'input[name="date"]',
            'input[name="Date"]',
            '.date',
            '.timestamp',
            '#date',
            '#timestamp'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return "Unknown date"
    
    def extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all links from the email."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith(('http', 'mailto')):
                links.append(href)
        return links
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
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
    
    def save_cleaned_email(self, original_file: Path, cleaned_data: Dict[str, str]) -> Path:
        """
        Save cleaned email to output folder.
        
        Args:
            original_file: Original file path
            cleaned_data: Cleaned email data
            
        Returns:
            Path to saved file
        """
        # Create safe filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', original_file.stem)
        output_file = self.output_folder / f"{safe_name}_cleaned.txt"
        
        # Create content for the cleaned file
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
    
    def process_single_file(self, file_path: Path) -> Dict[str, str]:
        """
        Process a single email file.
        
        Args:
            file_path: Path to the email file
            
        Returns:
            Dictionary with processing results
        """
        self.logger.info(f"Processing: {file_path}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Clean the content
            cleaned_data = self.clean_html_content(content)
            
            # Save cleaned file
            saved_path = self.save_cleaned_email(file_path, cleaned_data)
            
            result = {
                'original_file': str(file_path),
                'cleaned_file': str(saved_path) if saved_path else None,
                'title': cleaned_data['title'],
                'subject': cleaned_data['subject'],
                'sender': cleaned_data['sender'],
                'word_count': cleaned_data['word_count'],
                'char_count': cleaned_data['char_count'],
                'links_count': len(cleaned_data['links']),
                'success': saved_path is not None
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return {
                'original_file': str(file_path),
                'cleaned_file': None,
                'title': "Error",
                'subject': "Error",
                'sender': "Error",
                'word_count': 0,
                'char_count': 0,
                'links_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def process_all_emails(self, extensions: List[str] = None) -> List[Dict[str, str]]:
        """
        Process all email files in the input folder.
        
        Args:
            extensions: List of file extensions to process
            
        Returns:
            List of processing results
        """
        self.logger.info("Starting email cleaning process...")
        
        # Find all email files
        email_files = self.find_email_files(extensions)
        
        if not email_files:
            self.logger.warning("No email files found to process")
            return []
        
        results = []
        
        for file_path in email_files:
            result = self.process_single_file(file_path)
            results.append(result)
            
            # Log progress
            if result['success']:
                self.logger.info(f"✅ Processed: {file_path.name}")
            else:
                self.logger.error(f"❌ Failed: {file_path.name}")
        
        # Log summary
        successful = sum(1 for r in results if r['success'])
        self.logger.info(f"Processing complete: {successful}/{len(results)} files processed successfully")
        
        return results
    
    def generate_summary_report(self, results: List[Dict[str, str]]) -> Path:
        """
        Generate a summary report of the cleaning process.
        
        Args:
            results: List of processing results
            
        Returns:
            Path to the summary report
        """
        report_file = self.output_folder / "cleaning_summary.txt"
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        total_words = sum(r['word_count'] for r in successful)
        total_chars = sum(r['char_count'] for r in successful)
        total_links = sum(r['links_count'] for r in successful)
        
        report_content = f"""EMAIL CLEANING SUMMARY REPORT
==============================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total files processed: {len(results)}
- Successfully cleaned: {len(successful)}
- Failed: {len(failed)}
- Success rate: {len(successful)/len(results)*100:.1f}%

STATISTICS:
- Total words extracted: {total_words:,}
- Total characters: {total_chars:,}
- Total links found: {total_links}

SUCCESSFUL FILES:
{chr(10).join(f"- {Path(r['original_file']).name} -> {Path(r['cleaned_file']).name}" for r in successful)}

FAILED FILES:
{chr(10).join(f"- {Path(r['original_file']).name}: {r.get('error', 'Unknown error')}" for r in failed)}
"""
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Summary report saved: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Error saving summary report: {str(e)}")
            return None


def main():
    """Main function to run email cleaning."""
    print("📧 Email Cleaning Script")
    print("=" * 40)
    
    # Initialize cleaner
    cleaner = EmailCleaner(
        input_folder="gdrive_access/output",  # Where your raw emails are
        output_folder="cleaned_emails"  # Where to save cleaned files
    )
    
    # Process all email files
    print("🔍 Looking for email files...")
    results = cleaner.process_all_emails()
    
    if not results:
        print("❌ No email files found in the input folder")
        print("💡 Make sure you have email files in the 'gdrive_access/output' folder")
        return
    
    # Generate summary report
    print("📊 Generating summary report...")
    report_path = cleaner.generate_summary_report(results)
    
    # Print summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n✅ Processing complete!")
    print(f"📁 Files processed: {len(results)}")
    print(f"✅ Successfully cleaned: {successful}")
    print(f"❌ Failed: {len(results) - successful}")
    print(f"📄 Summary report: {report_path}")
    print(f"📁 Cleaned files saved to: {cleaner.output_folder}")


if __name__ == "__main__":
    main()
