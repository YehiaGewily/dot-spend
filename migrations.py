import shutil
import datetime
from pathlib import Path
from rich import print as rprint
from rich.progress import track
from datastore import JSONDataStore, SQLiteDataStore, DataStore
from config import get_data_path, get_db_path, get_budget_path

def migrate_json_to_sqlite():
    """Migrate data from JSON files to SQLite database."""
    json_store = JSONDataStore()
    sqlite_store = SQLiteDataStore()
    
    rprint("[bold cyan]Starting migration: JSON -> SQLite[/bold cyan]")
    
    # 1. Backup JSON
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_data_path().parent / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if get_data_path().exists():
            shutil.copy2(get_data_path(), backup_dir / "expenses.json")
        if get_budget_path().exists():
            shutil.copy2(get_budget_path(), backup_dir / "budgets.json")
        rprint(f"[green]✔ Backup created at:[/green] {backup_dir}")
    except Exception as e:
        rprint(f"[red]Backup failed:[/red] {e}")
        return False

    # 2. Extract Data
    expenses = json_store.get_expenses()
    budgets = json_store.load_budgets()
    
    if not expenses and not budgets:
        rprint("[yellow]No data to migrate.[/yellow]")
        return True

    # 3. Insert into SQLite
    try:
        # Clear existing SQLite data to avoid duplicates if re-running
        sqlite_store.clear_all_expenses()
        
        # Expenses
        for item in track(expenses, description="Migrating expenses..."):
            sqlite_store.add_expense(
                amount=item['amount'],
                category=item['category'],
                note=item.get('note', ''),
                timestamp=item['timestamp']
            )
            
        # Budgets
        sqlite_store.save_budgets(budgets)
        
        rprint("[bold green]✔ Migration successful![/bold green]")
        return True
        
    except Exception as e:
        rprint(f"[bold red]Migration failed:[/bold red] {e}")
        # Ideally rollback here, but we cleared data.
        # Since we have JSON backup, user allows retry.
        return False

def migrate_sqlite_to_json():
    """Migrate data from SQLite database to JSON files."""
    json_store = JSONDataStore()
    sqlite_store = SQLiteDataStore()

    rprint("[bold cyan]Starting migration: SQLite -> JSON[/bold cyan]")
    
    # 1. Backup SQLite
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_data_path().parent / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if get_db_path().exists():
            shutil.copy2(get_db_path(), backup_dir / "expenses.db")
        rprint(f"[green]✔ Backup created at:[/green] {backup_dir}")
    except Exception as e:
        rprint(f"[red]Backup failed:[/red] {e}")
        return False
        
    # 2. Extract Data
    expenses = sqlite_store.get_expenses()
    budgets = sqlite_store.load_budgets()

    if not expenses and not budgets:
         rprint("[yellow]No data to migrate.[/yellow]")
         return True
         
    # 3. Write to JSON
    try:
        # We need to manually inject for JSON store because its add_expense generates new IDs
        # To preserve IDs, we should use internal methods or just overwrite the file
        
        # Transform for JSON format
        json_expenses = []
        for item in track(expenses, description="Migrating expenses..."):
            # Ensure format matches JSON expectation
            # SQLite might return dict-like rows
            entry = dict(item)
            # Ensure 'date' field exists if missing
            if 'date' not in entry and 'timestamp' in entry:
                 entry['date'] = datetime.datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M")
            json_expenses.append(entry)
            
        json_store._save_data(json_expenses)
        json_store.save_budgets(budgets)
        
        rprint("[bold green]✔ Migration successful![/bold green]")
        return True
        
    except Exception as e:
        rprint(f"[bold red]Migration failed:[/bold red] {e}")
        return False
