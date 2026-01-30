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
import typer
import json

history_manager = HistoryManager()

# Initialize App and UI
app = typer.Typer(add_completion=False)
console = Console()

# --- DATA HANDLING ---
def load_data():
    path = get_data_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Migration: Ensure all have ID and timestamp (ISO)
        migrated = False
        for item in data:
            if 'id' not in item:
                item['id'] = str(uuid.uuid4())[:8]
                migrated = True
            
            # Ensure 'timestamp' field is the ISO date string for filtering
            # Old data had 'timestamp' as float and 'date' as string
            # We want 'timestamp' to be the robust ISO string used for ID
            # Let's keep 'date' as the display string for backwards compat if we want,
            # or standardize.
            # Requirement says: "timestamp (ISO format)"
            
            if isinstance(item.get('timestamp'), float):
                # Convert old float timestamp to ISO
                dt = datetime.datetime.fromtimestamp(item['timestamp'])
                item['timestamp'] = dt.isoformat()
                migrated = True
            elif 'timestamp' not in item:
                # Use date string if available
                dt = parse_date(item['date']) if 'date' in item else datetime.datetime.now()
                item['timestamp'] = dt.isoformat() if dt else datetime.datetime.now().isoformat()
                migrated = True
                
        if migrated:
            save_data(data)
            
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    path = get_data_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

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
    
    budgets = load_budgets()
    cat_key = category.upper()
    
    budgets[cat_key] = {
        "amount": amount,
        "period": period,
        "created": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    save_budgets(budgets)
    rprint(f"[bold green]✔ Budget set:[/bold green] {cat_key} - ${amount} ({period})")

@budget_app.command("list")
def budget_list():
    """List all active budgets."""
    budgets = load_budgets()
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
    budgets = load_budgets()
    cat_key = category.upper()
    
    if cat_key in budgets:
        del budgets[cat_key]
        save_budgets(budgets)
        rprint(f"[bold red]Deleted budget for:[/bold red] {cat_key}")
    else:
        rprint(f"[red]No budget found for:[/red] {cat_key}")

@budget_app.command("clear")
def budget_clear():
    """Remove all budgets."""
    if typer.confirm("Are you sure you want to delete ALL budgets?"):
        save_budgets({})
        rprint("[bold red]All budgets cleared.[/bold red]")

@budget_app.command("status")
def budget_status():
    """Check budget status."""
    budgets = load_budgets()
    data = load_data()
    
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

def load_budgets():
    path = get_budget_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_budgets(data):
    path = get_budget_path()
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
        "id": str(uuid.uuid4())[:8],
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), # Display friendly
        "timestamp": datetime.datetime.now().isoformat(), # Filter friendly ISO
        "amount": amount,
        "category": category.upper(),
        "note": note
    }

    data.append(entry)
    save_data(data)

    save_data(data)
    
    # Log transaction
    history_manager.log_transaction(
        action="add",
        expense_id=entry['id'],
        expense=entry
    )

    rprint(f"[bold green]✔ Added:[/bold green] {category} - ${amount}")

    # Budget Check
    budgets = load_budgets()
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
    data = load_data()
    
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
    data = load_data()
    if not data:
        rprint("[red]No data to delete.[/red]")
        return

    # Find and delete
    target = None
    for item in data:
        if item['id'] == expense_id:
            target = item
            break
    
    if target:
        data.remove(target)
        save_data(data)
        
        # Log transaction
        history_manager.log_transaction(
            action="delete",
            expense_id=target['id'],
            expense=target
        )
        
        rprint(f"[bold red]Deleted:[/bold red] {target['note']} - ${target['amount']}")
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
    data = load_data()
    target = None
    target_index = -1
    
    for i, item in enumerate(data):
        if item['id'] == expense_id:
            target = item
            target_index = i
            break
            
    if not target:
        rprint(f"[bold red]Error:[/bold red] Expense ID {expense_id} not found.")
        return

    # Capture before state (deepcopy to be safe)
    before_state = target.copy()
    
    # Apply changes
    changes = []
    if amount is not None:
        target['amount'] = amount
        changes.append(f"Amount: ${before_state['amount']} -> ${amount}")
    if category is not None:
        target['category'] = category.upper()
        changes.append(f"Category: {before_state['category']} -> {category.upper()}")
    if note is not None:
        target['note'] = note
        changes.append(f"Note: {before_state['note']} -> {note}")
    if date is not None:
        new_date = parse_date(date)
        if new_date:
            target['date'] = new_date.strftime("%Y-%m-%d %H:%M")
            target['timestamp'] = new_date.isoformat()
            changes.append(f"Date: {before_state['date']} -> {target['date']}")
        else:
            rprint(f"[red]Invalid date format:[/red] {date}")
            return

    if not changes:
        rprint("[yellow]No changes made.[/yellow]")
        return
        
    # Confirmation
    rprint(f"[bold yellow]Changes to be made:[/bold yellow]")
    for change in changes:
        rprint(f" - {change}")
        
    if typer.confirm("Apply these changes?"):
        data[target_index] = target
        save_data(data)
        
        # Log transaction
        history_manager.log_transaction(
            action="edit",
            expense_id=expense_id,
            before=before_state,
            after=target
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

    for _ in range(steps):
        last_tx = history_manager.pop_last_transaction()
        if not last_tx:
            rprint("[yellow]Nothing to undo (history empty).[/yellow]")
            break
            
        action = last_tx['action']
        expense_id = last_tx['expense_id']
        rprint(f"Undoing [bold]{action}[/bold] on ID {expense_id}...", end=" ")
        
        data = load_data()
        
        if action == 'add':
            # Reverse of add is delete
            data = [item for item in data if item['id'] != expense_id]
            save_data(data)
            rprint("[green]Done (Removed)[/green]")
            
        elif action == 'delete':
            # Reverse of delete is re-add
            # We need the full object which we stored in 'expense'
            if 'expense' in last_tx:
                data.append(last_tx['expense'])
                save_data(data)
                rprint("[green]Done (Restored)[/green]")
            else:
                rprint("[red]Failed (Missing backup data)[/red]")

        elif action == 'edit':
            # Reverse of edit is returning to 'before' state
            if 'before' in last_tx:
                # Find current item (if it still exists)
                found = False
                for i, item in enumerate(data):
                    if item['id'] == expense_id:
                        data[i] = last_tx['before']
                        found = True
                        break
                
                if found:
                    save_data(data)
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
    data = load_data()
    budgets = load_budgets()
    
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
    data = load_data()
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
    data = load_data()
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
        save_data([])
        rprint("[bold red]💥 Data nuked.[/bold red]")


if __name__ == "__main__":
    init_storage()
    app()