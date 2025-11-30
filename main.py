import typer
import json
import csv
import datetime
import plotext as plt
from pathlib import Path
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
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    path = get_data_path()
    with open(path, 'w', encoding='utf-8') as f:
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

    rprint(f"[bold green]✔ Added:[/bold green] {category} - ${amount}")


# FIX: We rename the function to 'view_expenses' to avoid breaking Python's 'list' keyword
# The 'name="list"' part ensures the CLI command is still 'spend list'
@app.command(name="list")
def view_expenses(
    last: int = typer.Option(10, "--last", "-l", help="Show last N expenses")
):
    """
    View expenses with IDs.
    """
    data = load_data()
    
    if not data:
        rprint("[yellow]No expenses found.[/yellow]")
        return

    sorted_data = sorted(data, key=lambda x: x['timestamp'], reverse=True)
    
    table = Table(title="Expense History", style="cyan", box=None)
    
    table.add_column("ID", style="bold white", justify="right")
    table.add_column("Date", style="dim", justify="left")
    table.add_column("Category", style="magenta", justify="left")
    table.add_column("Note", style="white", justify="left")
    table.add_column("Amount", style="green", justify="right")

    display_data = sorted_data[:last]

    for index, item in enumerate(display_data):
        table.add_row(
            str(index + 1),
            item['date'], 
            item['category'], 
            item['note'], 
            f"${item['amount']:.2f}"
        )

    console.print(table)


@app.command()
def delete(
    item_id: int = typer.Argument(..., help="The ID number from the 'list' command")
):
    """
    Delete an expense by its ID number.
    """
    data = load_data()
    if not data:
        rprint("[red]No data to delete.[/red]")
        return

    sorted_data = sorted(data, key=lambda x: x['timestamp'], reverse=True)

    try:
        target_entry = sorted_data[item_id - 1]
        data.remove(target_entry)
        save_data(data)
        rprint(f"[bold red]Deleted:[/bold red] {target_entry['note']} - ${target_entry['amount']}")
    except IndexError:
        rprint(f"[bold red]Error:[/bold red] ID {item_id} does not exist.")


@app.command()
def graph():
    """
    Visualize spending.
    """
    data = load_data()
    if not data:
        rprint("[yellow]No data to graph.[/yellow]")
        return

    categories = {}
    for item in data:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + item['amount']

    # Now this works because 'list' refers to Python's list tool again
    keys = list(categories.keys())
    values = list(categories.values())

    plt.simple_bar(keys, values, width=60, title="Spending by Category")
    plt.show()


@app.command()
def export(
    path: str = typer.Argument("export.csv", help="Path or filename to save the CSV")
):
    """
    Export data to CSV.
    """
    data = load_data()
    if not data:
        rprint("[yellow]No data to export.[/yellow]")
        return

    target_path = Path(path)

    if target_path.is_dir():
        target_path = target_path / "expenses.csv"
        
    if not target_path.parent.exists():
        rprint(f"[red]Error:[/red] The folder '{target_path.parent}' does not exist.")
        return

    # Define the columns we want (readable ones only)
    fieldnames = ["date", "category", "note", "amount"]
    
    try:
        with open(target_path, 'w', newline='', encoding='utf-8') as f:
            # extrasaction='ignore' tells csv to skip the 'timestamp' field
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        rprint(f"[bold green]✔ Exported to:[/bold green] {target_path.absolute()}")
    except Exception as e:
        rprint(f"[red]Error exporting:[/red] {e}")


@app.command()
def status(
    style: str = typer.Option("text", "--style", "-s", help="Output style: text, polybar, json")
):
    """
    Get daily total.
    """
    data = load_data()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    daily_total = sum(item['amount'] for item in data if item['date'].startswith(today))

    if style == "polybar":
        rprint(f"%{{F#ff5555}}💸 ${daily_total:.2f}%{{F-}}")
    elif style == "json":
        print(json.dumps({"text": f"${daily_total:.2f}", "class": "expense"}))
    else:
        rprint(f"[bold]Today:[/bold] ${daily_total:.2f}")


@app.command()
def nuke():
    """
    Delete ALL data.
    """
    confirm = typer.confirm("Are you sure you want to delete ALL expenses?")
    if confirm:
        save_data([])
        rprint("[bold red]💥 Data nuked.[/bold red]")


if __name__ == "__main__":
    init_storage()
    app()