"""UX utilities for progress indicators and confirmations."""
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import typer
from contextlib import contextmanager

console = Console()

@contextmanager
def spinner(message: str):
    """Show a spinner during long operations."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        yield

def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    return typer.confirm(message, default=default)

def success(message: str):
    """Print success message."""
    rprint(f"[bold green]✓[/bold green] {message}")

def warning(message: str):
    """Print warning message."""
    rprint(f"[bold yellow]⚠[/bold yellow] {message}")

def error(message: str):
    """Print error message."""
    rprint(f"[bold red]✗[/bold red] {message}")

def info(message: str):
    """Print info message."""
    rprint(f"[bold blue]ℹ[/bold blue] {message}")

def tip(message: str):
    """Print tip message."""
    rprint(f"[bold cyan]💡[/bold cyan] {message}")
