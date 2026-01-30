from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Label, Input, DataTable, Static, ProgressBar
from textual.screen import Screen
from textual.reactive import reactive
from textual.message import Message
import datetime
from datastore import DataStoreFactory
from uuid import uuid4

class Dashboard(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Welcome to Dot Spend", id="welcome"),
            Horizontal(
                Static("Today: $0.00", id="stat-today", classes="stat-box"),
                Static("This Week: $0.00", id="stat-week", classes="stat-box"),
                Static("This Month: $0.00", id="stat-month", classes="stat-box"),
            ),
            Label("Recent Expenses", classes="section-title"),
            DataTable(id="recent-table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        store = DataStoreFactory.get_store()
        data = store.get_expenses()
        today = datetime.date.today()
        
        # Calculate stats
        total_today = sum(d['amount'] for d in data if d['timestamp'].startswith(today.isoformat()[:10]))
        # (Simplified week/month logic for MVP)
        total_month = sum(d['amount'] for d in data if d['timestamp'].startswith(today.strftime("%Y-%m")))

        self.query_one("#stat-today", Static).update(f"Today\n${total_today:.2f}")
        self.query_one("#stat-month", Static).update(f"Month\n${total_month:.2f}")

        # Recent Table
        table = self.query_one("#recent-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Date", "Category", "Amount", "Note")
        for item in sorted(data, key=lambda x: x['timestamp'], reverse=True)[:5]:
             table.add_row(item['date'], item['category'], f"${item['amount']:.2f}", item['note'])

class AddExpense(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Add New Expense", classes="title"),
            Input(placeholder="Amount", id="amount", type="number"),
            Input(placeholder="Category", id="category"),
            Input(placeholder="Note", id="note"),
            Horizontal(
                Button("Save", variant="primary", id="save"),
                Button("Cancel", variant="error", id="cancel"),
            ),
            id="add-form"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_expense()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def save_expense(self) -> None:
        amount_str = self.query_one("#amount", Input).value
        category = self.query_one("#category", Input).value
        note = self.query_one("#note", Input).value
        
        if not amount_str or not category:
            self.notify("Amount and Category are required!", severity="error")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            self.notify("Invalid amount", severity="error")
            return

        store = DataStoreFactory.get_store()
        store.add_expense(
            amount=amount,
            category=category,
            note=note,
            timestamp=datetime.datetime.now().isoformat()
        )
        
        self.notify("Expense added!")
        self.app.pop_screen()
        # Trigger refresh on dashboard if needed (or app activate)

class ExpenseList(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search...", id="search")
        yield DataTable(id="expenses-table")
        yield Footer()

    def on_mount(self) -> None:
        self.load_table()

    def load_table(self, query="") -> None:
        table = self.query_one("#expenses-table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "Date", "Category", "Amount", "Note")
        
        store = DataStoreFactory.get_store()
        data = store.get_expenses()
        for item in sorted(data, key=lambda x: x['timestamp'], reverse=True):
            if query.lower() in item['note'].lower() or query.lower() in item['category'].lower():
                table.add_row(item['id'], item['date'], item['category'], f"${item['amount']:.2f}", item['note'])
    
    def on_input_changed(self, event: Input.Changed) -> None:
        self.load_table(event.value)

class DotSpendApp(App):
    CSS_PATH = "tui.tcss"
    BINDINGS = [
        ("d", "switch_mode('dashboard')", "Dashboard"),
        ("a", "switch_mode('add')", "Add Expense"),
        ("l", "switch_mode('list')", "Expenses"),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.install_screen(Dashboard(), name="dashboard")
        self.install_screen(AddExpense(), name="add")
        self.install_screen(ExpenseList(), name="list")
        self.push_screen("dashboard")

    def action_switch_mode(self, mode: str) -> None:
        if mode == "add":
            self.push_screen("add")
        else:
            self.switch_screen(mode)
            # Refresh data if switching to dashboard or list
            if mode == "dashboard":
                self.get_screen("dashboard").refresh_data()
            elif mode == "list":
                 self.get_screen("list").load_table()

if __name__ == "__main__":
    app = DotSpendApp()
    app.run()
