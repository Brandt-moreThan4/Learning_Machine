"""
Quiz export module for generating and exporting quizzes.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import csv
from datetime import datetime

from .config import Config
from .generators import get_quiz_generator


class QuizExporter:
    """Class to generate and export quizzes."""
    
    def __init__(self, config: Config):
        """Initialize the quiz exporter."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_quizzes(
        self, 
        input_dir: Path, 
        output_dir: Path, 
        quiz_type: str = "template_first",
        questions: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate quizzes from processed emails."""
        self.logger.info(f"Generating quizzes from: {input_dir}")
        
        if not input_dir.exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return []
        
        # Find processed email files
        email_files = list(input_dir.glob("*_processed.json"))
        
        if not email_files:
            self.logger.warning("No processed email files found")
            return []
        
        # Get quiz generator
        generator = get_quiz_generator(quiz_type, self.config)
        
        if not generator:
            self.logger.error(f"Unknown quiz type: {quiz_type}")
            return []
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for email_file in email_files:
            try:
                # Load processed email
                with open(email_file, 'r', encoding='utf-8') as f:
                    email_data = json.load(f)
                
                # Generate quiz
                quiz = generator.generate_quiz(email_data, questions)
                
                if quiz:
                    # Save quiz
                    quiz_file = self._save_quiz(quiz, email_data, output_dir)
                    if quiz_file:
                        results.append({
                            'source_file': str(email_file),
                            'quiz_file': str(quiz_file),
                            'quiz_type': quiz_type,
                            'questions_count': len(quiz.get('questions', [])),
                            'generated_at': datetime.now().isoformat()
                        })
                        self.logger.info(f"Generated quiz: {quiz_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error generating quiz for {email_file.name}: {str(e)}")
        
        self.logger.info(f"Quiz generation complete: {len(results)} quizzes generated")
        return results
    
    def _save_quiz(self, quiz: Dict[str, Any], email_data: Dict[str, Any], output_dir: Path) -> Optional[Path]:
        """Save quiz to file."""
        try:
            # Create filename
            source_name = Path(email_data['file_name']).stem.replace('_processed', '')
            quiz_file = output_dir / f"{source_name}_quiz.json"
            
            # Add metadata
            quiz['metadata'] = {
                'source_file': email_data['file_name'],
                'source_title': email_data['metadata'].get('title', 'Unknown'),
                'source_subject': email_data['metadata'].get('subject', 'Unknown'),
                'generated_at': datetime.now().isoformat(),
                'quiz_type': quiz.get('type', 'unknown')
            }
            
            # Save quiz
            with open(quiz_file, 'w', encoding='utf-8') as f:
                json.dump(quiz, f, indent=2, ensure_ascii=False)
            
            return quiz_file
            
        except Exception as e:
            self.logger.error(f"Error saving quiz: {str(e)}")
            return None
    
    def export_quizzes(self, input_dir: Path, output_file: Path, format: str = "json") -> bool:
        """Export quizzes to various formats."""
        self.logger.info(f"Exporting quizzes from: {input_dir}")
        
        if not input_dir.exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return False
        
        # Find quiz files
        quiz_files = list(input_dir.glob("*_quiz.json"))
        
        if not quiz_files:
            self.logger.warning("No quiz files found")
            return False
        
        # Load all quizzes
        quizzes = []
        for quiz_file in quiz_files:
            try:
                with open(quiz_file, 'r', encoding='utf-8') as f:
                    quiz_data = json.load(f)
                quizzes.append(quiz_data)
            except Exception as e:
                self.logger.error(f"Error loading quiz {quiz_file.name}: {str(e)}")
        
        if not quizzes:
            self.logger.error("No valid quiz files found")
            return False
        
        # Export based on format
        try:
            if format.lower() == "json":
                return self._export_json(quizzes, output_file)
            elif format.lower() == "csv":
                return self._export_csv(quizzes, output_file)
            elif format.lower() == "html":
                return self._export_html(quizzes, output_file)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            self.logger.error(f"Error exporting quizzes: {str(e)}")
            return False
    
    def _export_json(self, quizzes: List[Dict[str, Any]], output_file: Path) -> bool:
        """Export quizzes as JSON."""
        export_data = {
            'quizzes': quizzes,
            'export_info': {
                'total_quizzes': len(quizzes),
                'exported_at': datetime.now().isoformat(),
                'format': 'json'
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(quizzes)} quizzes to JSON: {output_file}")
        return True
    
    def _export_csv(self, quizzes: List[Dict[str, Any]], output_file: Path) -> bool:
        """Export quizzes as CSV."""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Quiz ID', 'Source File', 'Title', 'Subject', 'Question Count',
                'Quiz Type', 'Generated At'
            ])
            
            # Write quiz data
            for i, quiz in enumerate(quizzes):
                metadata = quiz.get('metadata', {})
                writer.writerow([
                    f"quiz_{i+1}",
                    metadata.get('source_file', 'Unknown'),
                    metadata.get('source_title', 'Unknown'),
                    metadata.get('source_subject', 'Unknown'),
                    len(quiz.get('questions', [])),
                    quiz.get('type', 'unknown'),
                    metadata.get('generated_at', 'Unknown')
                ])
        
        self.logger.info(f"Exported {len(quizzes)} quizzes to CSV: {output_file}")
        return True
    
    def _export_html(self, quizzes: List[Dict[str, Any]], output_file: Path) -> bool:
        """Export quizzes as HTML."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Email Quizzes Export</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .quiz {{ border: 1px solid #ddd; margin: 20px 0; padding: 20px; }}
        .question {{ margin: 15px 0; }}
        .options {{ margin: 10px 0; }}
        .option {{ margin: 5px 0; }}
        .correct {{ color: green; font-weight: bold; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
    </style>
</head>
<body>
    <h1>Email Quizzes Export</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Total Quizzes: {len(quizzes)}</p>
"""
        
        for i, quiz in enumerate(quizzes):
            metadata = quiz.get('metadata', {})
            questions = quiz.get('questions', [])
            
            html_content += f"""
    <div class="quiz">
        <h2>Quiz {i+1}: {metadata.get('source_title', 'Unknown')}</h2>
        <p><strong>Source:</strong> {metadata.get('source_file', 'Unknown')}</p>
        <p><strong>Subject:</strong> {metadata.get('source_subject', 'Unknown')}</p>
        <p><strong>Type:</strong> {quiz.get('type', 'unknown')}</p>
        <p><strong>Questions:</strong> {len(questions)}</p>
"""
            
            for j, question in enumerate(questions):
                html_content += f"""
        <div class="question">
            <h3>Question {j+1}: {question.get('question', 'No question')}</h3>
            <div class="options">
"""
                
                for k, option in enumerate(question.get('options', [])):
                    is_correct = option.get('correct', False)
                    correct_class = 'correct' if is_correct else ''
                    html_content += f'                <div class="option {correct_class}">{chr(65+k)}. {option.get("text", "")}</div>\n'
                
                html_content += f"""
            </div>
            <p><strong>Explanation:</strong> {question.get('explanation', 'No explanation provided')}</p>
        </div>
"""
            
            html_content += "    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Exported {len(quizzes)} quizzes to HTML: {output_file}")
        return True
