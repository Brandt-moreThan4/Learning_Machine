"""
Command-line interface for Email Quizzer.
"""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .ingest import EmailIngester
from .process import EmailProcessor
from .validate import EmailValidator
from .export import QuizExporter

app = typer.Typer(
    name="email-quizzer",
    help="A tool for processing emails and generating quizzes from their content.",
    add_completion=False,
)

console = Console()


def setup_logging(config: Config) -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.logging.file) if config.logging.file else logging.NullHandler()
        ]
    )


@app.command()
def ingest(
    folder_id: Optional[str] = typer.Option(None, help="Google Drive folder ID to ingest from"),
    max_files: int = typer.Option(50, help="Maximum number of files to process"),
    config_file: Optional[str] = typer.Option(None, help="Path to configuration file"),
) -> None:
    """Ingest emails from Google Drive and clean them."""
    # Load configuration
    config = Config.from_env(config_file)
    setup_logging(config)
    
    # Create necessary directories
    config.create_directories()
    
    console.print("📧 [bold blue]Email Ingestion[/bold blue]")
    console.print("=" * 50)
    
    # Initialize ingester
    ingester = EmailIngester(config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Ingesting emails...", total=None)
        
        # Ingest emails
        results = ingester.ingest_emails(folder_id, max_files)
    
    if not results:
        console.print("❌ [red]No emails were processed[/red]")
        return
    
    # Display results
    successful = sum(1 for r in results if r['success'])
    console.print(f"\n✅ [green]Processing complete![/green]")
    console.print(f"📁 Files processed: {len(results)}")
    console.print(f"✅ Successfully cleaned: {successful}")
    console.print(f"❌ Failed: {len(results) - successful}")
    
    # Show summary table
    if results:
        table = Table(title="Email Processing Summary")
        table.add_column("File", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Words", justify="right", style="green")
        table.add_column("Status", style="red")
        
        for result in results[:10]:  # Show first 10
            status = "✅" if result['success'] else "❌"
            table.add_row(
                Path(result['original_file']).name[:30] + "...",
                result['title'][:30] + "..." if len(result['title']) > 30 else result['title'],
                str(result['word_count']),
                status
            )
        
        console.print(table)
        
        if len(results) > 10:
            console.print(f"... and {len(results) - 10} more files")


@app.command()
def process(
    input_dir: Optional[str] = typer.Option(None, help="Directory containing cleaned emails"),
    config_file: Optional[str] = typer.Option(None, help="Path to configuration file"),
) -> None:
    """Process cleaned emails for quiz generation."""
    # Load configuration
    config = Config.from_env(config_file)
    setup_logging(config)
    
    console.print("🔄 [bold blue]Email Processing[/bold blue]")
    console.print("=" * 50)
    
    # Initialize processor
    processor = EmailProcessor(config)
    
    # Process emails
    input_path = Path(input_dir) if input_dir else Path(config.data.cleaned_emails_dir)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing emails...", total=None)
        
        results = processor.process_emails(input_path)
    
    if not results:
        console.print("❌ [red]No emails were processed[/red]")
        return
    
    console.print(f"\n✅ [green]Processing complete![/green]")
    console.print(f"📁 Files processed: {len(results)}")


@app.command()
def validate(
    input_dir: Optional[str] = typer.Option(None, help="Directory containing emails to validate"),
    config_file: Optional[str] = typer.Option(None, help="Path to configuration file"),
) -> None:
    """Validate email content quality."""
    # Load configuration
    config = Config.from_env(config_file)
    setup_logging(config)
    
    console.print("✅ [bold blue]Email Validation[/bold blue]")
    console.print("=" * 50)
    
    # Initialize validator
    validator = EmailValidator(config)
    
    # Validate emails
    input_path = Path(input_dir) if input_dir else Path(config.data.cleaned_emails_dir)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Validating emails...", total=None)
        
        results = validator.validate_emails(input_path)
    
    if not results:
        console.print("❌ [red]No emails were validated[/red]")
        return
    
    # Display validation results
    valid_count = sum(1 for r in results if r['is_valid'])
    console.print(f"\n✅ [green]Validation complete![/green]")
    console.print(f"📁 Files validated: {len(results)}")
    console.print(f"✅ Valid: {valid_count}")
    console.print(f"❌ Invalid: {len(results) - valid_count}")


@app.command()
def generate(
    quiz_type: str = typer.Option("template_first", help="Type of quiz to generate"),
    questions: int = typer.Option(5, help="Number of questions to generate"),
    input_dir: Optional[str] = typer.Option(None, help="Directory containing processed emails"),
    output_dir: Optional[str] = typer.Option(None, help="Directory to save generated quizzes"),
    config_file: Optional[str] = typer.Option(None, help="Path to configuration file"),
) -> None:
    """Generate quizzes from processed emails."""
    # Load configuration
    config = Config.from_env(config_file)
    setup_logging(config)
    
    console.print("🎯 [bold blue]Quiz Generation[/bold blue]")
    console.print("=" * 50)
    
    # Initialize exporter
    exporter = QuizExporter(config)
    
    # Generate quizzes
    input_path = Path(input_dir) if input_dir else Path(config.data.cleaned_emails_dir)
    output_path = Path(output_dir) if output_dir else Path(config.data.quizzes_dir)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating quizzes...", total=None)
        
        results = exporter.generate_quizzes(
            input_path, 
            output_path, 
            quiz_type, 
            questions
        )
    
    if not results:
        console.print("❌ [red]No quizzes were generated[/red]")
        return
    
    console.print(f"\n✅ [green]Quiz generation complete![/green]")
    console.print(f"📁 Quizzes generated: {len(results)}")
    console.print(f"📂 Saved to: {output_path}")


@app.command()
def export(
    format: str = typer.Option("json", help="Export format (json, csv, html)"),
    input_dir: Optional[str] = typer.Option(None, help="Directory containing quizzes"),
    output_file: Optional[str] = typer.Option(None, help="Output file path"),
    config_file: Optional[str] = typer.Option(None, help="Path to configuration file"),
) -> None:
    """Export quizzes to various formats."""
    # Load configuration
    config = Config.from_env(config_file)
    setup_logging(config)
    
    console.print("📤 [bold blue]Quiz Export[/bold blue]")
    console.print("=" * 50)
    
    # Initialize exporter
    exporter = QuizExporter(config)
    
    # Export quizzes
    input_path = Path(input_dir) if input_dir else Path(config.data.quizzes_dir)
    output_path = Path(output_file) if output_file else Path(f"quizzes.{format}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting quizzes...", total=None)
        
        result = exporter.export_quizzes(input_path, output_path, format)
    
    if result:
        console.print(f"\n✅ [green]Export complete![/green]")
        console.print(f"📁 Exported to: {output_path}")
    else:
        console.print("❌ [red]Export failed[/red]")


@app.command()
def status(
    config_file: Optional[str] = typer.Option(None, help="Path to configuration file"),
) -> None:
    """Show project status and statistics."""
    # Load configuration
    config = Config.from_env(config_file)
    
    console.print("📊 [bold blue]Project Status[/bold blue]")
    console.print("=" * 50)
    
    # Get paths
    paths = config.get_paths()
    
    # Check directory status
    table = Table(title="Directory Status")
    table.add_column("Directory", style="cyan")
    table.add_column("Path", style="magenta")
    table.add_column("Exists", justify="center", style="green")
    table.add_column("Files", justify="right", style="blue")
    
    for name, path in paths.items():
        exists = "✅" if path.exists() else "❌"
        file_count = len(list(path.glob("*"))) if path.exists() else 0
        table.add_row(name, str(path), exists, str(file_count))
    
    console.print(table)
    
    # Show configuration summary
    console.print(f"\n📋 [bold]Configuration Summary[/bold]")
    console.print(f"Quiz Type: {config.quiz.default_quiz_type}")
    console.print(f"Questions: {config.quiz.questions_count}")
    console.print(f"Difficulty: {config.quiz.difficulty}")
    console.print(f"Output Format: {config.output.format}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
