import typer
import json
import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from config import init_storage, get_data_path

# Initialize App and UI
app = typer.Typer(add_completion=False)
console = Console()

# --- DATA HANDLING ---
def load_data():
    path = get_data_path()
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    path = get_data_path()
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# --- COMMANDS ---

@app.command()
def add(
    amount: float = typer.Option(..., "--amount", "-a", help="The expense amount"),
    category: str = typer.Option(..., "--category", "-c", help="Category (Food, Tech, Travel)"),
    note: str = typer.Option("", "--note", "-n", help="Short description")
):
    """
    Add a new expense.
    """
    init_storage()
    data = load_data()

    entry = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "timestamp": datetime.datetime.now().timestamp(),
        "amount": amount,
        "category": category.upper(),
        "note": note
    }

    data.append(entry)
    save_data(data)

    # Success Message
    rprint(f"[bold green]✔ Added:[/bold green] {category} - ${amount}")


@app.command()
def list(
    last: int = typer.Option(10, "--last", "-l", help="Show last N expenses")
):
    """
    View recent expenses in a table.
    """
    data = load_data()
    
    if not data:
        rprint("[yellow]No expenses found. Start spending![/yellow]")
        return

    # Create a nice table
    table = Table(title="Expense History", style="cyan", box=None) # box=None looks cleaner on CLI

    table.add_column("Date", style="dim", justify="left")
    table.add_column("Category", style="magenta", justify="left")
    table.add_column("Note", style="white", justify="left")
    table.add_column("Amount", style="green", justify="right")

    # Sort by timestamp descending (newest first) and take last N
    sorted_data = sorted(data, key=lambda x: x['timestamp'], reverse=True)[:last]

    for item in sorted_data:
        table.add_row(
            item['date'], 
            item['category'], 
            item['note'], 
            f"${item['amount']:.2f}"
        )

    console.print(table)


@app.command()
def status(
    style: str = typer.Option("text", "--style", "-s", help="Output style: text, polybar, json")
):
    """
    Get daily total for status bars (Polybar/Rainmeter).
    """
    data = load_data()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Calculate daily total
    daily_total = sum(item['amount'] for item in data if item['date'].startswith(today))

    if style == "polybar":
        # Arch Linux Polybar format
        rprint(f"%{{F#ff5555}}💸 ${daily_total:.2f}%{{F-}}")
    elif style == "json":
        # JSON for custom widgets
        print(json.dumps({"text": f"${daily_total:.2f}", "class": "expense"}))
    else:
        # Standard text (Windows/Default)
        rprint(f"[bold]Today:[/bold] ${daily_total:.2f}")

@app.command()
def nuke():
    """
    Delete all data (Reset).
    """
    confirm = typer.confirm("Are you sure you want to delete ALL expenses?")
    if confirm:
        save_data([])
        rprint("[bold red]💥 Data nuked.[/bold red]")

if __name__ == "__main__":
    init_storage()
    app()
    