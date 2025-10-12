"""
Email validation module for quality assessment.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from .config import Config


class EmailValidator:
    """Class to validate email content quality."""
    
    def __init__(self, config: Config):
        """Initialize the email validator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_emails(self, input_dir: Path) -> List[Dict[str, Any]]:
        """Validate cleaned emails for quality."""
        self.logger.info(f"Validating emails from: {input_dir}")
        
        if not input_dir.exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return []
        
        # Find all cleaned email files
        email_files = list(input_dir.glob("*_cleaned.txt"))
        
        if not email_files:
            self.logger.warning("No cleaned email files found")
            return []
        
        self.logger.info(f"Found {len(email_files)} email files to validate")
        
        results = []
        for email_file in email_files:
            try:
                validation = self._validate_single_email(email_file)
                results.append(validation)
                self.logger.info(f"Validated: {email_file.name}")
            except Exception as e:
                self.logger.error(f"Error validating {email_file.name}: {str(e)}")
                results.append({
                    'file_path': str(email_file),
                    'file_name': email_file.name,
                    'is_valid': False,
                    'errors': [f"Validation error: {str(e)}"],
                    'warnings': [],
                    'score': 0.0
                })
        
        self.logger.info(f"Validation complete: {len(results)} files validated")
        return results
    
    def _validate_single_email(self, email_file: Path) -> Dict[str, Any]:
        """Validate a single email file."""
        try:
            with open(email_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata and content
            metadata = self._extract_metadata(content)
            text_content = self._extract_text_content(content)
            
            # Perform validation checks
            errors = []
            warnings = []
            
            # Check 1: Content length
            if len(text_content) < 100:
                errors.append("Content too short (less than 100 characters)")
            elif len(text_content) < 500:
                warnings.append("Content relatively short (less than 500 characters)")
            
            # Check 2: Word count
            word_count = len(text_content.split())
            if word_count < 20:
                errors.append("Too few words (less than 20)")
            elif word_count < 100:
                warnings.append("Relatively few words (less than 100)")
            
            # Check 3: Metadata completeness
            if metadata['title'] == "No title" or metadata['title'] == "Unknown":
                warnings.append("Missing or unclear title")
            
            if metadata['subject'] == "No subject found" or metadata['subject'] == "Unknown":
                warnings.append("Missing or unclear subject")
            
            if metadata['sender'] == "Unknown sender":
                warnings.append("Unknown sender")
            
            # Check 4: Content quality
            quality_issues = self._check_content_quality(text_content)
            errors.extend(quality_issues['errors'])
            warnings.extend(quality_issues['warnings'])
            
            # Check 5: Structure
            structure_issues = self._check_structure(text_content)
            errors.extend(structure_issues['errors'])
            warnings.extend(structure_issues['warnings'])
            
            # Calculate overall score
            score = self._calculate_validation_score(text_content, errors, warnings)
            
            # Determine if valid
            is_valid = len(errors) == 0 and score >= 0.5
            
            return {
                'file_path': str(email_file),
                'file_name': email_file.name,
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'score': score,
                'metadata': metadata,
                'word_count': word_count,
                'char_count': len(text_content),
                'validated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error validating {email_file.name}: {str(e)}")
            return {
                'file_path': str(email_file),
                'file_name': email_file.name,
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'score': 0.0
            }
    
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
    
    def _check_content_quality(self, text: str) -> Dict[str, List[str]]:
        """Check content quality issues."""
        errors = []
        warnings = []
        
        # Check for excessive whitespace
        if re.search(r'\s{5,}', text):
            warnings.append("Excessive whitespace detected")
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', text):
            warnings.append("Repeated characters detected")
        
        # Check for HTML remnants
        if re.search(r'<[^>]+>', text):
            warnings.append("HTML tags detected in content")
        
        # Check for email artifacts
        if re.search(r'^\s*On\s+.*?wrote:', text, re.MULTILINE):
            warnings.append("Email reply artifacts detected")
        
        # Check for encoding issues
        if re.search(r'[^\x00-\x7F]', text):
            # Check for common encoding issues
            if re.search(r'â€™|â€œ|â€', text):
                warnings.append("Possible encoding issues detected")
        
        # Check for empty or very short sentences
        sentences = re.split(r'[.!?]+', text)
        short_sentences = [s for s in sentences if len(s.strip()) < 10]
        if len(short_sentences) > len(sentences) * 0.5:
            warnings.append("Many very short sentences detected")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_structure(self, text: str) -> Dict[str, List[str]]:
        """Check text structure issues."""
        errors = []
        warnings = []
        
        # Check for paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            warnings.append("Very few paragraphs (less than 2)")
        
        # Check for sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) < 3:
            errors.append("Too few sentences (less than 3)")
        elif len(sentences) < 5:
            warnings.append("Few sentences (less than 5)")
        
        # Check for proper sentence endings
        proper_endings = len(re.findall(r'[.!?]\s', text))
        if proper_endings < len(sentences) * 0.8:
            warnings.append("Many sentences without proper endings")
        
        # Check for capitalization
        sentences_with_caps = len(re.findall(r'^[A-Z]', text, re.MULTILINE))
        if sentences_with_caps < len(sentences) * 0.7:
            warnings.append("Many sentences without proper capitalization")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _calculate_validation_score(self, text: str, errors: List[str], warnings: List[str]) -> float:
        """Calculate overall validation score."""
        score = 1.0
        
        # Deduct for errors
        score -= len(errors) * 0.3
        
        # Deduct for warnings
        score -= len(warnings) * 0.1
        
        # Bonus for good content length
        word_count = len(text.split())
        if word_count > 200:
            score += 0.1
        elif word_count > 500:
            score += 0.2
        
        # Bonus for good structure
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) > 10:
            score += 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def save_validation_results(self, results: List[Dict[str, Any]], output_dir: Path) -> None:
        """Save validation results to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual results
        for result in results:
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', result['file_name'])
            output_file = output_dir / f"{safe_name}_validation.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary_file = output_dir / "validation_summary.json"
        valid_count = sum(1 for r in results if r['is_valid'])
        avg_score = sum(r['score'] for r in results) / len(results) if results else 0
        
        summary = {
            'total_emails': len(results),
            'valid_emails': valid_count,
            'invalid_emails': len(results) - valid_count,
            'average_score': avg_score,
            'validated_at': datetime.now().isoformat(),
            'files': [r['file_name'] for r in results]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved validation summary: {summary_file}")
