"""
Configuration management for Email Quizzer.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class GoogleDriveConfig(BaseModel):
    """Google Drive API configuration."""
    service_account_file: str = Field(default="service_account.json")
    output_folder: str = Field(default="output")
    cleaned_folder: str = Field(default="cleaned_emails")


class DataConfig(BaseModel):
    """Data directory configuration."""
    data_dir: str = Field(default="data")
    raw_emails_dir: str = Field(default="data/raw_emails")
    cleaned_emails_dir: str = Field(default="data/cleaned_emails")
    quizzes_dir: str = Field(default="data/quizzes")


class QuizConfig(BaseModel):
    """Quiz generation configuration."""
    default_quiz_type: str = Field(default="template_first")
    questions_count: int = Field(default=5, ge=1, le=50)
    difficulty: str = Field(default="medium")


class LLMConfig(BaseModel):
    """LLM configuration for quiz generation."""
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-3.5-turbo")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama2")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    file: Optional[str] = Field(default="logs/email_quizzer.log")


class OutputConfig(BaseModel):
    """Output configuration."""
    format: str = Field(default="json")
    include_metadata: bool = Field(default=True)
    save_intermediate_files: bool = Field(default=True)


class Config(BaseModel):
    """Main configuration class."""
    google_drive: GoogleDriveConfig = Field(default_factory=GoogleDriveConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    quiz: QuizConfig = Field(default_factory=QuizConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        return cls(
            google_drive=GoogleDriveConfig(
                service_account_file=os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE", "service_account.json"),
                output_folder=os.getenv("GOOGLE_DRIVE_OUTPUT_FOLDER", "output"),
                cleaned_folder=os.getenv("GOOGLE_DRIVE_CLEANED_FOLDER", "cleaned_emails"),
            ),
            data=DataConfig(
                data_dir=os.getenv("DATA_DIR", "data"),
                raw_emails_dir=os.getenv("RAW_EMAILS_DIR", "data/raw_emails"),
                cleaned_emails_dir=os.getenv("CLEANED_EMAILS_DIR", "data/cleaned_emails"),
                quizzes_dir=os.getenv("QUIZZES_DIR", "data/quizzes"),
            ),
            quiz=QuizConfig(
                default_quiz_type=os.getenv("DEFAULT_QUIZ_TYPE", "template_first"),
                questions_count=int(os.getenv("QUIZ_QUESTIONS_COUNT", "5")),
                difficulty=os.getenv("QUIZ_DIFFICULTY", "medium"),
            ),
            llm=LLMConfig(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                ollama_model=os.getenv("OLLAMA_MODEL", "llama2"),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file=os.getenv("LOG_FILE", "logs/email_quizzer.log"),
            ),
            output=OutputConfig(
                format=os.getenv("OUTPUT_FORMAT", "json"),
                include_metadata=os.getenv("INCLUDE_METADATA", "true").lower() == "true",
                save_intermediate_files=os.getenv("SAVE_INTERMEDIATE_FILES", "true").lower() == "true",
            ),
        )
    
    def get_paths(self) -> Dict[str, Path]:
        """Get all configured paths as Path objects."""
        return {
            "data_dir": Path(self.data.data_dir),
            "raw_emails_dir": Path(self.data.raw_emails_dir),
            "cleaned_emails_dir": Path(self.data.cleaned_emails_dir),
            "quizzes_dir": Path(self.data.quizzes_dir),
            "google_drive_output": Path(self.google_drive.output_folder),
            "google_drive_cleaned": Path(self.google_drive.cleaned_folder),
        }
    
    def create_directories(self) -> None:
        """Create all necessary directories."""
        paths = self.get_paths()
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if logging to file
        if self.logging.file:
            log_path = Path(self.logging.file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
