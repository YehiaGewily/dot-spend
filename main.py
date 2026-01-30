import typer
import json
import csv
import datetime
import plotext as plt
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich import print as rprint
import uuid
from config import init_storage, get_data_path, get_budget_path
from utils import get_date_range, filter_data_by_date, parse_date
from history import HistoryManager
from exporters import ExportManager
from insights import InsightsEngine
from datastore import DataStoreFactory
from migrations import migrate_json_to_sqlite, migrate_sqlite_to_json
from importers.csv_importer import CSVImporter
from importers.excel_importer import ExcelImporter
from importers.ofx_importer import OFXImporter
from categorization import RuleCategorizer, MLCategorizer
from deduplication import DuplicateDetector
from sync.manager import SyncManager
from recurring import RecurringManager

history_manager = HistoryManager()

# Initialize App and UI
app = typer.Typer(add_completion=False)
console = Console()

# --- DATA HANDLING ---
# Moved to data.py

# --- BUDGET LOGIC ---
budget_app = typer.Typer(help="Manage budgets")
app.add_typer(budget_app, name="budget")

def get_spending_for_period(category: str, period: str, data: list) -> float:
    now = datetime.datetime.now()
    if period == "monthly":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "weekly":
        # Monday is 0
        start_date = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        return 0.0

    total = 0.0
    for item in data:
        if item['category'].upper() == category.upper():
            item_date = datetime.datetime.strptime(item['date'], "%Y-%m-%d %H:%M")
            if item_date >= start_date:
                total += item['amount']
    return total

@budget_app.command("set")
def budget_set(
    category: str = typer.Option(..., "--category", "-c", help="Category to budget for"),
    amount: float = typer.Option(..., "--amount", "-a", help="Budget amount"),
    period: str = typer.Option("monthly", "--period", "-p", help="monthly or weekly")
):
    """Set a budget for a category."""
    if period not in ["monthly", "weekly"]:
        rprint("[red]Error: Period must be 'monthly' or 'weekly'[/red]")
        return
    
    store = DataStoreFactory.get_store()
    budgets = store.load_budgets()
    cat_key = category.upper()
    
    budgets[cat_key] = {
        "amount": amount,
        "period": period,
        "created": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    store.save_budgets(budgets)
    rprint(f"[bold green]✔ Budget set:[/bold green] {cat_key} - ${amount} ({period})")

@budget_app.command("list")
def budget_list():
    """List all active budgets."""
    store = DataStoreFactory.get_store()
    budgets = store.load_budgets()
    if not budgets:
        rprint("[yellow]No budgets set.[/yellow]")
        return
        
    table = Table(title="Active Budgets", style="magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Amount", style="green")
    table.add_column("Period", style="white")
    table.add_column("Created", style="dim")
    
    for cat, info in budgets.items():
        table.add_row(cat, f"${info['amount']:.2f}", info['period'], info['created'])
        
    console.print(table)

@budget_app.command("delete")
def budget_delete(
    category: str = typer.Option(..., "--category", "-c", help="Category to remove budget for")
):
    """Delete a budget."""
    store = DataStoreFactory.get_store()
    budgets = store.load_budgets()
    cat_key = category.upper()
    
    if cat_key in budgets:
        del budgets[cat_key]
        store.save_budgets(budgets)
        rprint(f"[bold red]Deleted budget for:[/bold red] {cat_key}")
    else:
        rprint(f"[red]No budget found for:[/red] {cat_key}")

@budget_app.command("clear")
def budget_clear():
    """Remove all budgets."""
    if typer.confirm("Are you sure you want to delete ALL budgets?"):
        store = DataStoreFactory.get_store()
        store.save_budgets({})
        rprint("[bold red]All budgets cleared.[/bold red]")

@budget_app.command("status")
@budget_app.command("status")
def budget_status():
    """Check budget status."""
    store = DataStoreFactory.get_store()
    budgets = store.load_budgets()
    data = store.get_expenses()
    
    if not budgets:
        rprint("[yellow]No budgets set.[/yellow]")
        return

    table = Table(title="Budget Status")
    table.add_column("Category", style="cyan")
    table.add_column("Budget", style="blue")
    table.add_column("Spent", style="magenta")
    table.add_column("Remaining", style="green")
    table.add_column("Status", style="bold")

    for cat, info in budgets.items():
        spent = get_spending_for_period(cat, info['period'], data)
        budget_amt = info['amount']
        remaining = budget_amt - spent
        percent = (spent / budget_amt) * 100 if budget_amt > 0 else 0
        
        status_color = "green"
        if percent >= 100:
            status_color = "red"
        elif percent >= 80:
            status_color = "yellow"
            
        status_msg = f"[{status_color}]{percent:.1f}%[/{status_color}]"
        
        if remaining < 0:
            rem_str = f"[red]-${abs(remaining):.2f}[/red]"
        else:
            rem_str = f"${remaining:.2f}"

        table.add_row(
            cat,
            f"${budget_amt:.2f}",
            f"${spent:.2f}",
            rem_str,
            status_msg
        )
        
    console.print(table)

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
    store = DataStoreFactory.get_store()

    entry = store.add_expense(
        amount=amount,
        category=category,
        note=note,
        timestamp=datetime.datetime.now().isoformat()
    )
    
    # Log transaction
    history_manager.log_transaction(
        action="add",
        expense_id=entry['id'],
        expense=entry
    )

    rprint(f"[bold green]✔ Added:[/bold green] {category} - ${amount}")

    # Budget Check
    budgets = store.load_budgets()
    data = store.get_expenses()
    cat_key = category.upper()
    if cat_key in budgets:
        info = budgets[cat_key]
        spent = get_spending_for_period(cat_key, info['period'], data)
        budget_amt = info['amount']
        
        if spent > budget_amt:
            rprint(f"[bold red]⚠ WARNING:[/bold red] Over budget for {cat_key}! ({info['period']})")
            rprint(f"  Spent: ${spent:.2f} / ${budget_amt:.2f}")
        elif spent >= budget_amt * 0.8:
            rprint(f"[bold yellow]⚠ ALERT:[/bold yellow] Nearing budget for {cat_key}.")
            rprint(f"  Spent: ${spent:.2f} / ${budget_amt:.2f}")


# FIX: We rename the function to 'view_expenses' to avoid breaking Python's 'list' keyword



# FIX: We rename the function to 'view_expenses' to avoid breaking Python's 'list' keyword
# The 'name="list"' part ensures the CLI command is still 'spend list'
@app.command(name="list")
def view_expenses(
    last: int = typer.Option(None, "--last", "-l", help="Show last N expenses (overrides date filters if set)"),
    from_date: str = typer.Option(None, "--from", help="Start date (ISO or common format)"),
    to_date: str = typer.Option(None, "--to", help="End date"),
    days: int = typer.Option(None, "--days", help="Show last N days"),
    today: bool = typer.Option(False, "--today", help="Show today's expenses"),
    yesterday: bool = typer.Option(False, "--yesterday", help="Show yesterday's expenses"),
    this_week: bool = typer.Option(False, "--this-week", help="Show this week's expenses"),
    last_week: bool = typer.Option(False, "--last-week", help="Show last week's expenses"),
    this_month: bool = typer.Option(False, "--this-month", help="Show this month's expenses"),
    last_month: bool = typer.Option(False, "--last-month", help="Show last month's expenses"),
    this_year: bool = typer.Option(False, "--this-year", help="Show this year's expenses"),
):
    """
    View expenses with date filtering.
    """
    store = DataStoreFactory.get_store()
    data = store.get_expenses()
    
    if not data:
        rprint("[yellow]No expenses found.[/yellow]")
        return

    # Filter by date
    start, end = get_date_range(
        from_date, to_date, days, today, yesterday, 
        this_week, last_week, this_month, last_month, this_year
    )
    
    filtered_data = filter_data_by_date(data, start, end)
    
    if not filtered_data:
        rprint("[yellow]No expenses found for this period.[/yellow]")
        return

    # Sort
    sorted_data = sorted(filtered_data, key=lambda x: x['timestamp'], reverse=True)
    
    # Apply limit if set
    if last:
        display_data = sorted_data[:last]
    else:
        display_data = sorted_data

    table = Table(title="Expense History", style="cyan", box=None)
    
    table.add_column("ID", style="bold white", justify="right")
    table.add_column("Date", style="dim", justify="left")
    table.add_column("Category", style="magenta", justify="left")
    table.add_column("Note", style="white", justify="left")
    table.add_column("Amount", style="green", justify="right")

    for item in display_data:
        table.add_row(
            item['id'],
            item['date'], 
            item['category'], 
            item['note'], 
            f"${item['amount']:.2f}"
        )

    console.print(table)


@app.command()
def delete(
    expense_id: str = typer.Argument(..., help="The ID (first 8 chars) of the expense to delete")
):
    """
    Delete an expense by its ID.
    """
    store = DataStoreFactory.get_store()
    target = store.get_expense(expense_id)
    
    if target:
        store.delete_expense(expense_id)
        
        # Log transaction
        history_manager.log_transaction(
            action="delete",
            expense_id=target['id'],
            expense=target
        )
        
        rprint(f"[bold red]Deleted:[/bold red] {target.get('note', '')} - ${target['amount']}")
    else:
        rprint(f"[bold red]Error:[/bold red] ID {expense_id} not found.")


@app.command()
def edit(
    expense_id: str = typer.Argument(..., help="The ID (first 8 chars) of the expense to edit"),
    amount: float = typer.Option(None, "--amount", "-a", help="New amount"),
    category: str = typer.Option(None, "--category", "-c", help="New category"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    date: str = typer.Option(None, "--date", "-d", help="New date (ISO or common format)")
):
    """
    Edit an existing expense.
    """
    store = DataStoreFactory.get_store()
    target = store.get_expense(expense_id)
            
    if not target:
        rprint(f"[bold red]Error:[/bold red] Expense ID {expense_id} not found.")
        return

    # Capture before state (deepcopy to be safe)
    before_state = target.copy()
    
    # Apply changes
    updates = {}
    changes = []
    
    if amount is not None:
        updates['amount'] = amount
        changes.append(f"Amount: ${before_state['amount']} -> ${amount}")
    if category is not None:
        updates['category'] = category.upper()
        changes.append(f"Category: {before_state['category']} -> {category.upper()}")
    if note is not None:
        updates['note'] = note
        changes.append(f"Note: {before_state.get('note', '')} -> {note}")
    if date is not None:
        new_date = parse_date(date)
        if new_date:
            updates['date'] = new_date.strftime("%Y-%m-%d %H:%M")
            updates['timestamp'] = new_date.isoformat()
            changes.append(f"Date: {before_state.get('date', '')} -> {updates['date']}")
        else:
            rprint(f"[red]Invalid date format:[/red] {date}")
            return

    if not updates:
        rprint("[yellow]No changes made.[/yellow]")
        return
        
    # Confirmation
    rprint(f"[bold yellow]Changes to be made:[/bold yellow]")
    for change in changes:
        rprint(f" - {change}")
        
    if typer.confirm("Apply these changes?"):
        store.update_expense(expense_id, updates)
        
        # Fetch updated for log
        after_state = store.get_expense(expense_id)
        
        # Log transaction
        history_manager.log_transaction(
            action="edit",
            expense_id=expense_id,
            before=before_state,
            after=after_state
        )
        rprint("[bold green]✔ Expense updated.[/bold green]")
    else:
        rprint("[yellow]Edit cancelled.[/yellow]")

@app.command()
def undo(
    steps: int = typer.Option(1, "--steps", help="Number of actions to undo")
):
    """
    Undo the last action(s).
    """
    if steps < 1:
        return

    store = DataStoreFactory.get_store()

    for _ in range(steps):
        last_tx = history_manager.pop_last_transaction()
        if not last_tx:
            rprint("[yellow]Nothing to undo (history empty).[/yellow]")
            break
            
        action = last_tx['action']
        expense_id = last_tx['expense_id']
        rprint(f"Undoing [bold]{action}[/bold] on ID {expense_id}...", end=" ")
        
        if action == 'add':
            # Reverse of add is delete
            if store.delete_expense(expense_id):
                rprint("[green]Done (Removed)[/green]")
            else:
                rprint("[red]Failed (Not found)[/red]")
            
        elif action == 'delete':
            # Reverse of delete is re-add
            if 'expense' in last_tx:
                exp = last_tx['expense']
                store.add_expense(
                    amount=exp['amount'],
                    category=exp['category'],
                    note=exp['note'],
                    timestamp=exp['timestamp'],
                    expense_id=exp['id']
                )
                rprint("[green]Done (Restored)[/green]")
            else:
                rprint("[red]Failed (Missing backup data)[/red]")

        elif action == 'edit':
            # Reverse of edit is returning to 'before' state
            if 'before' in last_tx:
                updates = last_tx['before']
                # We need to map 'date' back to timestamp if needed or just use updates directly
                # update_expense expects dict of fields to update.
                # 'before' has all fields.
                
                # Clean up updates dict if needed, or just pass it.
                # update_expense implementation in SQLite handles keys.
                # But 'id' shouldn't be updated.
                updates_clean = {k: v for k, v in updates.items() if k != 'id'}
                
                if store.update_expense(expense_id, updates_clean):
                    rprint("[green]Done (Reverted)[/green]")
                else:
                    rprint("[red]Failed (Item not found)[/red]")
            else:
                 rprint("[red]Failed (Missing state data)[/red]")

# --- HISTORY GROUP ---
history_app = typer.Typer(help="Manage transaction history")
app.add_typer(history_app, name="history")

@history_app.callback(invoke_without_command=True)
def history_main(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", "-l", help="Number of recent transactions to show"),
    all: bool = typer.Option(False, "--all", help="Show all transactions")
):
    """
    View transaction history.
    """
    if ctx.invoked_subcommand is not None:
        return

    txs = history_manager.get_history(limit=1000 if all else limit)
    
    if not txs:
        rprint("[yellow]No history found.[/yellow]")
        return
        
    table = Table(title="Transaction Log", style="cyan")
    table.add_column("Time", style="dim")
    table.add_column("Action", justify="center")
    table.add_column("ID", style="white")
    table.add_column("Details", style="magenta")
    
    for tx in reversed(txs):
        action = tx['action']
        style = "white"
        if action == "add": style = "green"
        elif action == "delete": style = "red"
        elif action == "edit": style = "yellow"
        
        details = ""
        if action == "edit":
            changes = []
            before = tx.get('before', {})
            after = tx.get('after', {})
            for k, v in after.items():
                if before.get(k) != v:
                    changes.append(f"{k}")
            details = f"Modified: {', '.join(changes)}"
        elif action == "add":
            details = f"{tx.get('expense', {}).get('category', '')} - ${tx.get('expense', {}).get('amount', 0)}"
        elif action == "delete":
            details = f"{tx.get('expense', {}).get('category', '')} - ${tx.get('expense', {}).get('amount', 0)}"

        table.add_row(
            tx['timestamp'][:16].replace('T', ' '),
            f"[{style}]{action.upper()}[/{style}]",
            tx['expense_id'],
            details
        )
        
    console.print(table)

@history_app.command("clear")
def history_clear():
    """
    Clear all transaction history.
    """
    if typer.confirm("Are you sure you want to clear ALL transaction history? (Cannot be undone)"):
        history_manager.clear_history()
        rprint("[bold red]History cleared.[/bold red]")

@app.command()
def graph(
    from_date: str = typer.Option(None, "--from", help="Start date"),
    to_date: str = typer.Option(None, "--to", help="End date"),
    days: int = typer.Option(None, "--days", help="Last N days"),
    today: bool = typer.Option(False, "--today", help="Today"),
    yesterday: bool = typer.Option(False, "--yesterday", help="Yesterday"),
    this_week: bool = typer.Option(False, "--this-week", help="This week"),
    last_week: bool = typer.Option(False, "--last-week", help="Last week"),
    this_month: bool = typer.Option(False, "--this-month", help="This month"),
    last_month: bool = typer.Option(False, "--last-month", help="Last month"),
    this_year: bool = typer.Option(False, "--this-year", help="This year"),
):
    """
    Visualize spending (Budget vs Actual).
    """
    store = DataStoreFactory.get_store()
    data = store.get_expenses()
    budgets = store.load_budgets()
    
    if not data:
        rprint("[yellow]No data to graph.[/yellow]")
        return

    # Filter by date
    start, end = get_date_range(
        from_date, to_date, days, today, yesterday, 
        this_week, last_week, this_month, last_month, this_year
    )
    
    filtered_data = filter_data_by_date(data, start, end)
    
    if not filtered_data:
        rprint("[yellow]No data for selected period.[/yellow]")
        return

    # Determine unique categories
    categories = set(item['category'] for item in filtered_data)
    # We might NOT want to show all budget categories if they don't have spend in this period?
    # Requirement: "Show budget vs actual". If we filter to "today", do we show all budget bars as empty?
    # Probably better to only show categories that have spending OR explicitly requested.
    # But usually graphs show active categories. Let's include active categories from specific data.
    # To keep it comparable to full budget, usually you want to see what you haven't spent on too?
    # Let's stick to categories present in the filtered data to avoid cluttering the graph with 0-value bars for irrelevant old budgets.
    # UNLESS we are in "this month" mode, where budget comparison is highly relevant.
    # For now, let's show categories present in filter + active budgets if it's a current-time filter?
    # Simpler approach: Just categories in data.
    
    # Actually, user wants to see budget vs actual. If actual is 0, user might still want to see the budget bar.
    # Let's add all budget keys IF the filter is "current period" relevance? Hard to guess.
    # Let's stick to categories in filtered_data to avoid confusion.
    # If a category has 0 spend in the filtered period, it won't show up.
    
    # Wait, if I want to check my budget status for the month, I want to see "Food: $0 / $500" if I haven't eaten yet.
    # Let's include budget keys as well to be safe, but only if they are relevant?
    # Let's just include all unique categories from data + budgets for consistent view.
    categories.update(budgets.keys())
    
    keys = sorted(list(categories))
    actuals = []
    budget_vals = []
    colors = []
    
    for cat in keys:
        b_info = budgets.get(cat)
        # Note: Budget is usually "monthly" or "weekly". 
        # Comparing a "custom date range" actual vs "monthly budget" is tricky.
        # Ideally we pro-rate the budget? Or just show the limit?
        # User prompt doesn't specify pro-rating. We will show the raw limit for context.
        
        limit = b_info['amount'] if b_info else 0
        
        # Calculate spend in the FILTERED data
        spent = sum(item['amount'] for item in filtered_data if item['category'] == cat)
        
        actuals.append(spent)
        budget_vals.append(limit)

        
        # Color coding
        if limit > 0:
            pct = spent / limit
            if pct > 1.0:
                colors.append("red")
            elif pct >= 0.8:
                colors.append("yellow")
            else:
                colors.append("green")
        else:
            colors.append("blue") # No budget

    plt.simple_bar(keys, actuals, width=60, title="Spending (Actual vs Budget Check)")
    plt.bar(keys, actuals, color=colors, label="Actual")
    # We can't easily overlay a 'line' in plotext simple_bar, but we can try a multi-bar if needed.
    # However, color coding the actuals is the main requirement.
    # To show the budget 'line', we could plot a second series?
    # plt.multiple_bar(keys, [actuals, budget_vals], label=["Actual", "Budget"], color=[colors, "white"])
    # But simple_bar is a wrapper. Let's use standard bar.
    
    plt.clear_figure()
    plt.bar(keys, actuals, color=colors, label="Actual")
    if any(budget_vals):
        plt.bar(keys, budget_vals, color="white", marker="o", label="Budget Limit") 
    
    plt.title(f"Spending Status (Color = Budget Health)")
    plt.show()


@app.command()
def export(
    path: str = typer.Option(".", "--output", "-o", help="Output path or filename. Defaults to current directory."),
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv, xlsx, json, pdf"),
    from_date: str = typer.Option(None, "--from", help="Start date"),
    to_date: str = typer.Option(None, "--to", help="End date"),
    days: int = typer.Option(None, "--days", help="Last N days"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    fields: str = typer.Option(None, "--fields", help="Comma-separated fields to include"),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
    template: str = typer.Option("simple", "--template", help="PDF template: simple, detailed"),
    open_file: bool = typer.Option(False, "--open", help="Open file after export")
):
    """
    Export data with advanced options (CSV, Excel, PDF, JSON).
    """
    store = DataStoreFactory.get_store()
    data = store.get_expenses()
    if not data:
        rprint("[yellow]No data to export.[/yellow]")
        return

    # Filter by date
    start, end = get_date_range(from_date, to_date, days)
    filtered_data = filter_data_by_date(data, start, end)

    # Filter by category
    if category:
        filtered_data = [d for d in filtered_data if d['category'].upper() == category.upper()]

    if not filtered_data:
        rprint("[yellow]No data matches the filter for export.[/yellow]")
        return

    # Delegate to ExportManager
    exporter = ExportManager(filtered_data)
    
    # Check if path is a directory or file
    # If it's a directory (default '.'), ExportManager handles filename generation
    # If it's a file, we use it.
    
    exported_path = exporter.export(
        format=format,
        path=path,
        fields=fields,
        delimiter=delimiter,
        template=template
    )
    
    if open_file and exported_path:
        rprint(f"Opening {exported_path}...")
        try:
            typer.launch(str(exported_path))
        except Exception as e:
            rprint(f"[red]Failed to open file:[/red] {e}")

@app.command()
def insights(
    basic: bool = typer.Option(False, "--basic", help="Show basic insights"),
    trends: bool = typer.Option(False, "--trends", help="Show trend analysis"),
    categories: bool = typer.Option(False, "--categories", help="Show category analysis"),
    predict: bool = typer.Option(False, "--predict", help="Show predictive insights"),
    time: bool = typer.Option(False, "--time", help="Show time-based analysis"),
    from_date: str = typer.Option(None, "--from", help="Start date"),
    to_date: str = typer.Option(None, "--to", help="End date"),
    days: int = typer.Option(None, "--days", help="Last N days"),
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
):
    """
    Show financial insights and trends.
    """
    store = DataStoreFactory.get_store()
    data = store.get_expenses()
    if not data:
        rprint("[yellow]No data available.[/yellow]")
        return

    # Filter by date
    start, end = get_date_range(from_date, to_date, days)
    filtered_data = filter_data_by_date(data, start, end)

    # Filter by category
    if category:
        filtered_data = [d for d in filtered_data if d['category'].upper() == category.upper()]

    if not filtered_data:
        rprint("[yellow]No data matches filter.[/yellow]")
        return
        
    engine = InsightsEngine(filtered_data, store.load_budgets())
    engine.run_command(basic, trends, categories, predict, time)


@app.command(name="interactive")
def interactive():
    """
    Launch the interactive terminal UI.
    """ 
    try:
        from tui import DotSpendApp
        app = DotSpendApp()
        app.run()
    except ImportError:
        rprint("[red]Error:[/red] Textual is not installed. Run 'pip install textual'.")
    except Exception as e:
        rprint(f"[red]Error launching TUI:[/red] {e}")

@app.command(name="tui")
def tui():
    """
    Launch the interactive terminal UI (alias).
    """
    interactive()


@app.command()
def summary(
    from_date: str = typer.Option(None, "--from", help="Start date"),
    to_date: str = typer.Option(None, "--to", help="End date"),
    days: int = typer.Option(None, "--days", help="Last N days"),
    today: bool = typer.Option(False, "--today", help="Today"),
    yesterday: bool = typer.Option(False, "--yesterday", help="Yesterday"),
    this_week: bool = typer.Option(False, "--this-week", help="This week"),
    last_week: bool = typer.Option(False, "--last-week", help="Last week"),
    this_month: bool = typer.Option(False, "--this-month", help="This month"),
    last_month: bool = typer.Option(False, "--last-month", help="Last month"),
    this_year: bool = typer.Option(False, "--this-year", help="This year"),
):
    """
    Show financial summary (Total, Avg/Day, Breakdown).
    """
    store = DataStoreFactory.get_store()
    data = store.get_expenses()
    start, end = get_date_range(
        from_date, to_date, days, today, yesterday, 
        this_week, last_week, this_month, last_month, this_year
    )
    filtered_data = filter_data_by_date(data, start, end)
    
    if not filtered_data:
        rprint("[yellow]No data for selected period.[/yellow]")
        return

    total_spent = sum(item['amount'] for item in filtered_data)
    
    # Calculate days count in range
    # If range is open-ended (start=None or end=None), we can use min/max of data or just default to 1?
    # Logic: If user said --this-month, we know start/end.
    # If user said nothing, it's all time.
    
    if start and end:
        # Inclusive days
        delta = (end - start).days + 1
        day_count = max(1, delta)
        # If 'end' is in future, we might want to cap at 'now'? 
        # Requirement doesn't specify, but typically "Average per day" for "This month" implies days passed so far?
        # Or days in the whole month? 
        # "Avg/Day: $39.82" -> usually implies spent / days_with_data or spent / days_in_window.
        # Let's use days_in_window for specific ranges like "Last month".
        # For "This month", usually it's days elapsed.
        if end > datetime.datetime.now():
            # Cap at today for "elapsed" average?
            # Let's stick to the window size for consistency, unless it leads to weird low averages.
            # Actually, most robust is (max_date - min_date) from data if no filter?
            pass
    elif filtered_data:
        # derive from data
        timestamps = [parse_date(x['timestamp']) for x in filtered_data]
        min_ts = min(timestamps)
        max_ts = max(timestamps)
        day_count = max(1, (max_ts - min_ts).days + 1)
    else:
        day_count = 1

    avg_per_day = total_spent / day_count

    # Breakdown
    by_category = {}
    for item in filtered_data:
        cat = item['category']
        by_category[cat] = by_category.get(cat, 0.0) + item['amount']

    # Header
    range_str = "Custom Range"
    if this_month: range_str = "This Month"
    elif last_month: range_str = "Last Month"
    elif today: range_str = "Today"
    elif days: range_str = f"Last {days} Days"
    elif not start and not end: range_str = "All Time"
    
    console.print(f"\n[bold underline]Summary for {range_str}[/bold underline]")
    console.print(f"Total Spent: [green]${total_spent:.2f}[/green]")
    console.print(f"Days: {day_count}")
    console.print(f"Avg/Day: [cyan]${avg_per_day:.2f}[/cyan]\n")
    
    # Table
    table = Table(title="Category Breakdown", show_header=False, box=None)
    table.add_column("Category", style="yellow")
    table.add_column("Amount", justify="right")
    table.add_column("Percent", justify="right")
    
    for cat, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        pct = (amount / total_spent) * 100
        table.add_row(
            f"{cat}:",
            f"${amount:.2f}",
            f"({pct:.1f}%)"
        )
    console.print(table)
    console.print("")


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
        store = DataStoreFactory.get_store()
        store.clear_all_expenses()
        rprint("[bold red]💥 Data nuked.[/bold red]")

# --- MIGRATION COMMANDS ---
migrate_app = typer.Typer(help="Manage data migration")
app.add_typer(migrate_app, name="migrate")

@migrate_app.command("to-sqlite")
def to_sqlite():
    """Migrate data from JSON to SQLite."""
    if typer.confirm("Migrate all data to SQLite? This will backup your JSON files first."):
        migrate_json_to_sqlite()

@migrate_app.command("to-json")
def to_json():
    """Migrate data from SQLite to JSON."""
    if typer.confirm("Migrate all data to JSON? This will backup your SQLite database first."):
        migrate_sqlite_to_json()

# --- CONFIG COMMAND ---
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")

@config_app.command("get")
def config_get(key: str = typer.Argument(..., help="Config key")):
    """Get a configuration value."""
    from config import load_settings
    settings = load_settings()
    val = settings.get(key)
    if val:
        rprint(f"{key} = [green]{val}[/green]")
    else:
        rprint(f"[red]Key '{key}' not set.[/red]")

@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value")
):
    """Set a configuration value."""
    from config import load_settings, save_settings
    settings = load_settings()
    
    if key == "storage":
        key = "storage_backend"
        if value not in ["json", "sqlite"]:
             rprint("[red]Invalid backend. data must be 'json' or 'sqlite'[/red]")
             return
             
    settings[key] = value
    save_settings(settings)
    rprint(f"[green]Set {key} = {value}[/green]")


# --- IMPORT COMMAND ---
@app.command(name="import")
def import_file(
    file_path: str = typer.Argument(..., help="Path to file (CSV, XLSX, OFX)"),
    format: str = typer.Option(None, "--format", "-f", help="Format: csv, xlsx, ofx"),
    mapping: str = typer.Option(None, "--mapping", "-m", help="Column mapping (JSON string or file path)"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview only"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive review"),
    skip_duplicates: bool = typer.Option(True, "--skip-duplicates/--no-skip", help="Skip duplicates"),
    invert_negative: bool = typer.Option(True, "--invert-negative", help="Invert negative amounts (expenses often negative in statements)"),
):
    """
    Import transactions from bank statements.
    """
    path = Path(file_path)
    if not path.exists():
        rprint(f"[red]File not found:[/red] {file_path}")
        return

    # Detect format
    if not format:
        suffix = path.suffix.lower()
        if suffix == '.csv': format = 'csv'
        elif suffix in ['.xlsx', '.xls']: format = 'xlsx'
        elif suffix == '.ofx': format = 'ofx'
        else:
            rprint("[red]Could not detect format. Specify --format.[/red]")
            return

    # Select Importer
    importer = None
    if format == 'csv': importer = CSVImporter()
    elif format == 'xlsx': importer = ExcelImporter()
    elif format == 'ofx': importer = OFXImporter()
    else:
        rprint(f"[red]Unsupported format:[/red] {format}")
        return

    rprint(f"[cyan]Parsing {format.upper()} file...[/cyan]")
    
    # Parse options
    # Mapping config handling (simplistic for now)
    mapping_dict = {}
    if mapping:
        import json
        try:
             # Try parsing as JSON string
             mapping_dict = json.loads(mapping)
        except:
             # Try reading file
             m_path = Path(mapping)
             if m_path.exists():
                 with open(m_path) as f:
                     mapping_dict = json.load(f)
    
    try:
        transactions = importer.parse(
            str(path), 
            mapping=mapping_dict, 
            invert_negative=invert_negative
        )
    except Exception as e:
        rprint(f"[red]Import failed:[/red] {e}")
        return
        
    if not transactions:
        rprint("[yellow]No transactions found.[/yellow]")
        return
        
    rprint(f"[green]Found {len(transactions)} transactions.[/green]")
    
    # Init storage & helpers
    store = DataStoreFactory.get_store()
    existing_data = store.get_expenses() # Need all for ML/Dedup
    
    deduper = DuplicateDetector(existing_data)
    rule_categorizer = RuleCategorizer() # Config path optional
    ml_categorizer = MLCategorizer()
    ml_categorizer.train(existing_data)
    
    new_txs = []
    
    # Process transactions
    stats = {"auto_cat": 0, "duplicates": 0, "new": 0}
    
    for tx in transactions:
        # Check Duplicate
        if skip_duplicates and deduper.is_duplicate(tx):
            stats["duplicates"] += 1
            continue
            
        # Auto-categorize
        cat = rule_categorizer.categorize(tx.description, tx.amount)
        if not cat:
            cat = ml_categorizer.predict(tx.description)
            
        if cat:
            tx.category = cat
            stats["auto_cat"] += 1
        
        new_txs.append(tx)
        stats["new"] += 1

    rprint(f"Stats: {stats['new']} new ({stats['auto_cat']} auto-categorized), {stats['duplicates']} duplicates skipped.")

    if preview:
        table = Table(title="Preview Import")
        table.add_column("Date")
        table.add_column("Desc")
        table.add_column("Amount")
        table.add_column("Category")
        for tx in new_txs[:10]:
            cat_style = "green" if tx.category else "red"
            cat_display = tx.category or "UNCATEGORIZED"
            table.add_row(
                tx.date[:10],
                tx.description,
                f"{tx.amount:.2f}",
                f"[{cat_style}]{cat_display}[/{cat_style}]"
            )
        console.print(table)
        if len(new_txs) > 10:
            rprint(f"... and {len(new_txs)-10} more.")
        return

    if interactive:
        # Interactive review logic
        # For MVP, maybe confirm bulk or iterate uncategorized
        # Let's iterate UNcataloged ones
        
        uncategorized = [t for t in new_txs if not t.category]
        if uncategorized:
            if typer.confirm(f"Review {len(uncategorized)} uncategorized transactions?"):
                 for tx in uncategorized:
                     cat = typer.prompt(f"Category for '{tx.description}' (${tx.amount})", default="General")
                     tx.category = cat
        
    # Final Confirm
    if not typer.confirm(f"Import {len(new_txs)} transactions?"):
        rprint("[yellow]Import cancelled.[/yellow]")
        return
        
    # Save
    count = 0
    for tx in new_txs:
        store.add_expense(
            amount=tx.amount,
            category=tx.category or "Uncategorized", 
            note=tx.description,
            timestamp=tx.date # ISO string
        )
        count += 1
        
    rprint(f"[bold green]Successfully imported {count} transactions![/bold green]")

# --- SYNC COMMAND ---
sync_app = typer.Typer(help="Cloud synchronization")
app.add_typer(sync_app, name="sync")

@sync_app.command("setup")
def sync_setup(
    provider: str = typer.Argument(..., help="Provider: google_drive, git, dropbox"),
    folder_id: str = typer.Option(None, help="Folder ID (Google Drive)"),
    repo: str = typer.Option(None, help="Repo URL/Path (Git)"),
    token: str = typer.Option(None, help="Auth Token (Dropbox)")
):
    """
    Setup cloud synchronization.
    """
    manager = SyncManager()
    
    # Interactive setup fallback
    if provider == "git" and not repo:
        from config import DATA_DIR
        repo = str(DATA_DIR)
        rprint(f"[cyan]Using data directory as git repo: {repo}[/cyan]")
    elif provider == "dropbox" and not token:
        token = typer.prompt("Enter Dropbox access token")
    
    data = {}
    if repo: data["repo_path"] = repo
    if token: data["token"] = token
    if folder_id: data["folder_id"] = folder_id

    try:
        manager.setup(provider, **data)
        rprint(f"[green]Sync setup with {provider} complete.[/green]")
    except Exception as e:
        rprint(f"[red]Setup failed:[/red] {e}")

@sync_app.command("enable")
def sync_enable():
    """Enable automatic sync."""
    # Toggle config
    manager = SyncManager()
    manager.config["enabled"] = True
    manager.save_config()
    rprint("[green]Sync enabled.[/green]")

@sync_app.command("disable")
def sync_disable():
    """Disable synchronization."""
    manager = SyncManager()
    manager.config["enabled"] = False
    manager.save_config()
    rprint("[yellow]Sync disabled.[/yellow]")

@sync_app.command("now")
def sync_now():
    """Run manual sync."""
    manager = SyncManager()
    if not manager.config.get("enabled"):
        rprint("[yellow]Sync is disabled. Enable it first.[/yellow]")
        return
        
    rprint("[cyan]Syncing...[/cyan]")
    # What to sync? The data files.
    from config import get_data_path, get_budget_path
    files = [str(get_data_path()), str(get_budget_path())]
    
    res = manager.sync_now(files)
    rprint(res)

@sync_app.command("status")
def sync_status():
    """Check sync status."""
    manager = SyncManager()
    enabled = manager.config.get("enabled", False)
    provider = manager.config.get("provider", "None")
    
    status_color = "green" if enabled else "yellow"
    rprint(f"Sync: [{status_color}]{'Enabled' if enabled else 'Disabled'}[/{status_color}]")
    rprint(f"Provider: {provider}")


# --- VERSION COMMAND ---
VERSION = "2.0.0"

@app.command()
def version():
    """Show version information."""
    rprint(f"[bold cyan]dot-spend[/bold cyan] version [green]{VERSION}[/green]")
    rprint("https://github.com/YehiaGewily/dot-spend")


# --- SHELL COMPLETIONS ---
completions_app = typer.Typer(help="Shell completion scripts")
app.add_typer(completions_app, name="completions")

BASH_COMPLETION = '''
_spend_completion() {
    local IFS=$'\\n'
    COMPREPLY=( $(env COMP_WORDS="${COMP_WORDS[*]}" \\
                      COMP_CWORD=$COMP_CWORD \\
                      _SPEND_COMPLETE=bash_complete $1) )
    return 0
}
complete -o default -F _spend_completion spend
'''

ZSH_COMPLETION = '''
#compdef spend
_spend() {
    eval $(env _SPEND_COMPLETE=zsh_source spend)
}
compdef _spend spend
'''

FISH_COMPLETION = '''
complete -c spend -f
complete -c spend -n "__fish_use_subcommand" -a "add" -d "Add expense"
complete -c spend -n "__fish_use_subcommand" -a "list" -d "List expenses"
complete -c spend -n "__fish_use_subcommand" -a "delete" -d "Delete expense"
complete -c spend -n "__fish_use_subcommand" -a "edit" -d "Edit expense"
complete -c spend -n "__fish_use_subcommand" -a "budget" -d "Budget management"
complete -c spend -n "__fish_use_subcommand" -a "insights" -d "Analytics"
complete -c spend -n "__fish_use_subcommand" -a "import" -d "Import data"
complete -c spend -n "__fish_use_subcommand" -a "export" -d "Export data"
complete -c spend -n "__fish_use_subcommand" -a "sync" -d "Cloud sync"
complete -c spend -n "__fish_use_subcommand" -a "tui" -d "Interactive mode"
complete -c spend -n "__fish_use_subcommand" -a "graph" -d "Visualize data"
complete -c spend -n "__fish_use_subcommand" -a "version" -d "Show version"
'''

@completions_app.command("show")
def completions_show(
    shell: str = typer.Argument(..., help="Shell: bash, zsh, fish")
):
    """Show completion script for a shell."""
    shell = shell.lower()
    if shell == "bash":
        print(BASH_COMPLETION)
    elif shell == "zsh":
        print(ZSH_COMPLETION)
    elif shell == "fish":
        print(FISH_COMPLETION)
    else:
        rprint(f"[red]Unknown shell:[/red] {shell}")
        rprint("Supported: bash, zsh, fish")

@completions_app.command("install")
def completions_install(
    shell: str = typer.Argument(..., help="Shell: bash, zsh, fish")
):
    """Install completion script for a shell."""
    import os
    home = os.path.expanduser("~")
    shell = shell.lower()
    
    if shell == "bash":
        path = os.path.join(home, ".bash_completion")
        with open(path, "a") as f:
            f.write(BASH_COMPLETION)
        rprint(f"[green]Bash completions added to {path}[/green]")
        rprint("Run: source ~/.bash_completion")
    elif shell == "zsh":
        path = os.path.join(home, ".zfunc", "_spend")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(ZSH_COMPLETION)
        rprint(f"[green]Zsh completions installed to {path}[/green]")
        rprint("Add to ~/.zshrc: fpath=(~/.zfunc $fpath); autoload -Uz compinit && compinit")
    elif shell == "fish":
        path = os.path.join(home, ".config", "fish", "completions", "spend.fish")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(FISH_COMPLETION)
        rprint(f"[green]Fish completions installed to {path}[/green]")
    else:
        rprint(f"[red]Unknown shell:[/red] {shell}")

# --- RECURRING EXPENSES ---
recurring_app = typer.Typer(help="Recurring expenses")
app.add_typer(recurring_app, name="recurring")

@recurring_app.command("add")
def recurring_add(
    amount: float = typer.Option(..., "--amount", "-a", help="Amount"),
    category: str = typer.Option(..., "--category", "-c", help="Category"),
    note: str = typer.Option("", "--note", "-n", help="Description"),
    frequency: str = typer.Option("monthly", "--frequency", "-f", help="daily/weekly/monthly/yearly"),
    day: int = typer.Option(1, "--day", help="Day of week (0-6) or month (1-31)"),
):
    """Add a recurring expense."""
    mgr = RecurringManager()
    rec_id = mgr.add(amount, category, note, frequency, day)
    rprint(f"[green]Recurring expense added: {rec_id}[/green]")
    rprint(f"  {frequency}: ${amount:.2f} - {category}")

@recurring_app.command("list")
def recurring_list():
    """List all recurring expenses."""
    mgr = RecurringManager()
    items = mgr.list_all()
    
    if not items:
        rprint("[yellow]No recurring expenses.[/yellow]")
        return
    
    table = Table(title="Recurring Expenses")
    table.add_column("ID", style="cyan")
    table.add_column("Amount", style="green")
    table.add_column("Category")
    table.add_column("Frequency")
    table.add_column("Status")
    
    for rec_id, rec in items:
        status = "[green]Active[/green]" if rec["active"] else "[yellow]Paused[/yellow]"
        table.add_row(
            rec_id,
            f"${rec['amount']:.2f}",
            rec["category"],
            f"{rec['frequency']} (day {rec['day']})",
            status
        )
    
    console.print(table)
    
    # Forecast
    forecast = mgr.forecast()
    rprint(f"\n[bold]Monthly forecast:[/bold] ${forecast:.2f}")

@recurring_app.command("delete")
def recurring_delete(rec_id: str = typer.Argument(..., help="Recurring ID")):
    """Delete a recurring expense."""
    mgr = RecurringManager()
    if mgr.delete(rec_id):
        rprint(f"[green]Deleted recurring expense: {rec_id}[/green]")
    else:
        rprint(f"[red]Not found: {rec_id}[/red]")

@recurring_app.command("pause")
def recurring_pause(rec_id: str = typer.Argument(..., help="Recurring ID")):
    """Pause a recurring expense."""
    mgr = RecurringManager()
    if mgr.pause(rec_id):
        rprint(f"[yellow]Paused: {rec_id}[/yellow]")
    else:
        rprint(f"[red]Not found: {rec_id}[/red]")

@recurring_app.command("resume")
def recurring_resume(rec_id: str = typer.Argument(..., help="Recurring ID")):
    """Resume a paused recurring expense."""
    mgr = RecurringManager()
    if mgr.resume(rec_id):
        rprint(f"[green]Resumed: {rec_id}[/green]")
    else:
        rprint(f"[red]Not found: {rec_id}[/red]")

@recurring_app.command("sync")
def recurring_sync():
    """Generate missing recurring expenses."""
    mgr = RecurringManager()
    store = DataStoreFactory.get_store()
    
    generated = mgr.sync_generate(store.add_expense)
    
    if generated:
        rprint(f"[green]Generated {len(generated)} recurring expenses.[/green]")
        for exp in generated:
            rprint(f"  - ${exp['amount']:.2f} {exp['category']}")
    else:
        rprint("[cyan]All recurring expenses up to date.[/cyan]")


# --- CURRENCY COMMANDS ---
from currency import CurrencyManager, SUPPORTED_CURRENCIES, CURRENCY_SYMBOLS

currency_app = typer.Typer(help="Currency management")
app.add_typer(currency_app, name="currency")

@currency_app.command("set")
def currency_set(currency: str = typer.Argument(..., help="Base currency code (USD, EUR, etc.)")):
    """Set base currency."""
    mgr = CurrencyManager()
    currency = currency.upper()
    if currency not in SUPPORTED_CURRENCIES:
        rprint(f"[red]Unsupported currency: {currency}[/red]")
        rprint(f"Supported: {', '.join(SUPPORTED_CURRENCIES[:10])}...")
        return
    
    if mgr.set_base(currency):
        rprint(f"[green]Base currency set to {currency}[/green]")
        mgr.update_rates()
        rprint("[cyan]Exchange rates updated.[/cyan]")

@currency_app.command("list")
def currency_list():
    """List supported currencies."""
    table = Table(title="Supported Currencies")
    table.add_column("Code", style="cyan")
    table.add_column("Symbol")
    
    for i in range(0, len(SUPPORTED_CURRENCIES), 4):
        row = []
        for j in range(4):
            if i + j < len(SUPPORTED_CURRENCIES):
                code = SUPPORTED_CURRENCIES[i + j]
                symbol = CURRENCY_SYMBOLS.get(code, "")
                row.append(f"{code} ({symbol})")
        if row:
            # Simplified display
            pass
    
    for code in SUPPORTED_CURRENCIES:
        symbol = CURRENCY_SYMBOLS.get(code, "")
        table.add_row(code, symbol)
    
    console.print(table)

@currency_app.command("rates")
def currency_rates():
    """Show current exchange rates."""
    mgr = CurrencyManager()
    
    if mgr.is_stale():
        rprint("[yellow]Warning: Exchange rates may be stale. Run 'spend currency update'.[/yellow]")
    
    rprint(f"[bold]Base currency:[/bold] {mgr.base_currency}")
    rprint(f"[bold]Last updated:[/bold] {mgr.config.get('last_update', 'Never')}")
    
    table = Table(title="Exchange Rates")
    table.add_column("Currency")
    table.add_column("Rate")
    
    rates = mgr.rates.get("rates", {})
    for code in ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]:
        if code in rates:
            table.add_row(code, f"{rates[code]:.4f}")
    
    console.print(table)

@currency_app.command("update")
def currency_update():
    """Update exchange rates from API."""
    mgr = CurrencyManager()
    rprint("[cyan]Fetching exchange rates...[/cyan]")
    
    if mgr.update_rates():
        rprint("[green]Exchange rates updated successfully.[/green]")
    else:
        rprint("[red]Failed to update rates. Using cached values.[/red]")


if __name__ == "__main__":
    init_storage()
    app()