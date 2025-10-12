"""
Email processing module for preparing emails for quiz generation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime

from .config import Config


class EmailProcessor:
    """Class to process cleaned emails for quiz generation."""
    
    def __init__(self, config: Config):
        """Initialize the email processor."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def process_emails(self, input_dir: Path) -> List[Dict[str, Any]]:
        """Process cleaned emails for quiz generation."""
        self.logger.info(f"Processing emails from: {input_dir}")
        
        if not input_dir.exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return []
        
        # Find all cleaned email files
        email_files = list(input_dir.glob("*_cleaned.txt"))
        
        if not email_files:
            self.logger.warning("No cleaned email files found")
            return []
        
        self.logger.info(f"Found {len(email_files)} email files to process")
        
        results = []
        for email_file in email_files:
            try:
                processed = self._process_single_email(email_file)
                if processed:
                    results.append(processed)
                    self.logger.info(f"Processed: {email_file.name}")
                else:
                    self.logger.warning(f"Failed to process: {email_file.name}")
            except Exception as e:
                self.logger.error(f"Error processing {email_file.name}: {str(e)}")
        
        self.logger.info(f"Processing complete: {len(results)}/{len(email_files)} files processed")
        return results
    
    def _process_single_email(self, email_file: Path) -> Optional[Dict[str, Any]]:
        """Process a single email file."""
        try:
            with open(email_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata and content
            metadata = self._extract_metadata(content)
            text_content = self._extract_text_content(content)
            
            if not text_content:
                self.logger.warning(f"No text content found in {email_file.name}")
                return None
            
            # Analyze content
            analysis = self._analyze_content(text_content)
            
            # Create processed email structure
            processed = {
                'file_path': str(email_file),
                'file_name': email_file.name,
                'metadata': metadata,
                'content': text_content,
                'analysis': analysis,
                'processed_at': datetime.now().isoformat(),
                'word_count': len(text_content.split()),
                'char_count': len(text_content)
            }
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error processing {email_file.name}: {str(e)}")
            return None
    
    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """Extract metadata from cleaned email content."""
        metadata = {}
        
        # Extract title
        title_match = re.search(r'Title:\s*(.+)', content)
        metadata['title'] = title_match.group(1).strip() if title_match else "Unknown"
        
        # Extract subject
        subject_match = re.search(r'Subject:\s*(.+)', content)
        metadata['subject'] = subject_match.group(1).strip() if subject_match else "Unknown"
        
        # Extract sender
        sender_match = re.search(r'Sender:\s*(.+)', content)
        metadata['sender'] = sender_match.group(1).strip() if sender_match else "Unknown"
        
        # Extract date
        date_match = re.search(r'Date:\s*(.+)', content)
        metadata['date'] = date_match.group(1).strip() if date_match else "Unknown"
        
        # Extract word count
        word_count_match = re.search(r'Word Count:\s*(\d+)', content)
        metadata['word_count'] = word_count_match.group(1) if word_count_match else "0"
        
        # Extract character count
        char_count_match = re.search(r'Character Count:\s*(\d+)', content)
        metadata['char_count'] = char_count_match.group(1) if char_count_match else "0"
        
        return metadata
    
    def _extract_text_content(self, content: str) -> str:
        """Extract the main text content from cleaned email."""
        # Find the "CLEANED TEXT:" section
        text_match = re.search(r'CLEANED TEXT:\s*\n\n(.+)', content, re.DOTALL)
        if text_match:
            return text_match.group(1).strip()
        
        # Fallback: extract everything after the last metadata line
        lines = content.split('\n')
        text_start = -1
        for i, line in enumerate(lines):
            if line.startswith('CLEANED TEXT:'):
                text_start = i + 2  # Skip the header and empty line
                break
        
        if text_start > 0:
            return '\n'.join(lines[text_start:]).strip()
        
        return ""
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze email content for quiz generation."""
        # Basic text analysis
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Extract potential quiz topics
        topics = self._extract_topics(text)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)
        
        # Extract numbers and dates
        numbers = re.findall(r'\b\d+\b', text)
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2},? \d{4}\b', text)
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len(paragraphs),
            'avg_words_per_sentence': len(words) / max(len([s for s in sentences if s.strip()]), 1),
            'topics': topics,
            'key_phrases': key_phrases,
            'numbers': numbers,
            'dates': dates,
            'readability_score': self._calculate_readability(text),
            'complexity_score': self._calculate_complexity(text)
        }
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract potential topics from text."""
        # Simple topic extraction based on common patterns
        topics = []
        
        # Look for capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        topics.extend(capitalized[:10])  # Limit to first 10
        
        # Look for common topic indicators
        topic_indicators = [
            r'about\s+(\w+)',
            r'topic\s+is\s+(\w+)',
            r'discussing\s+(\w+)',
            r'regarding\s+(\w+)'
        ]
        
        for pattern in topic_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend(matches)
        
        return list(set(topics))[:20]  # Remove duplicates and limit
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple key phrase extraction
        phrases = []
        
        # Look for quoted text
        quoted = re.findall(r'"([^"]+)"', text)
        phrases.extend(quoted)
        
        # Look for common phrase patterns
        phrase_patterns = [
            r'\b\w+\s+\w+\s+\w+\b',  # 3-word phrases
            r'\b\w+\s+\w+\b'  # 2-word phrases
        ]
        
        for pattern in phrase_patterns:
            matches = re.findall(pattern, text)
            phrases.extend(matches[:10])  # Limit each pattern
        
        return list(set(phrases))[:30]  # Remove duplicates and limit
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate a simple readability score."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0.0
        
        avg_words_per_sentence = len(words) / len([s for s in sentences if s.strip()])
        
        # Simple readability score (lower is more readable)
        return min(avg_words_per_sentence / 10.0, 1.0)
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate content complexity score."""
        words = text.split()
        
        if not words:
            return 0.0
        
        # Count complex words (3+ syllables approximation)
        complex_words = 0
        for word in words:
            if len(word) > 6:  # Simple heuristic
                complex_words += 1
        
        return min(complex_words / len(words), 1.0)
    
    def save_processed_emails(self, processed_emails: List[Dict[str, Any]], output_dir: Path) -> None:
        """Save processed emails to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for email in processed_emails:
            # Create filename
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', email['file_name'])
            output_file = output_dir / f"{safe_name}_processed.json"
            
            # Save as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(email, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved processed email: {output_file}")
        
        # Save summary
        summary_file = output_dir / "processing_summary.json"
        summary = {
            'total_emails': len(processed_emails),
            'processed_at': datetime.now().isoformat(),
            'total_words': sum(email['word_count'] for email in processed_emails),
            'total_chars': sum(email['char_count'] for email in processed_emails),
            'files': [email['file_name'] for email in processed_emails]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved processing summary: {summary_file}")
