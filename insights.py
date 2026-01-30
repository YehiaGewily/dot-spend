import datetime
import pandas as pd
import numpy as np
import plotext as plt
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich import box
from rich.text import Text
from rich.columns import Columns
from utils import parse_date

console = Console()

class InsightsEngine:
    def __init__(self, data, budgets=None):
        self.df = pd.DataFrame(data)
        if not self.df.empty:
            self.df['date_obj'] = self.df['timestamp'].apply(lambda x: parse_date(x))
            self.df['amount'] = pd.to_numeric(self.df['amount'])
        self.budgets = budgets or {}

    def get_dashboard(self):
        """Generates the full dashboard layout."""
        if self.df.empty:
            return Panel("No data available for insights.", title="Spend Insights", border_style="red")

        # Layout
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1)
        )
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        layout["left"].split(
            Layout(name="overview", ratio=1),
            Layout(name="trends", ratio=1)
        )
        layout["right"].split(
            Layout(name="categories", ratio=1),
            Layout(name="predictions", ratio=1)
        )

        # Content Generation
        header = self._generate_header()
        overview = self._generate_overview()
        trends = self._generate_trends()
        categories = self._generate_categories()
        predictions = self._generate_predictions()

        layout["header"].update(header)
        layout["overview"].update(Panel(overview, title="📊 Overview", border_style="blue"))
        layout["trends"].update(Panel(trends, title="📈 Trends", border_style="green"))
        layout["categories"].update(Panel(categories, title="🎯 Categories", border_style="yellow"))
        layout["predictions"].update(Panel(predictions, title="🔮 Predictions & Scores", border_style="magenta"))

        return layout

    def _generate_header(self):
        today = datetime.date.today().strftime("%B %Y")
        return Panel(f"[bold white]SPENDING INSIGHTS - {today.upper()}[/bold white]", style="on blue", box=box.HEAVY)

    def _generate_overview(self):
        total = self.df['amount'].sum()
        count = len(self.df)
        avg = self.df['amount'].mean()
        
        # Comparison with last month (if available) - mocked for simplicity if filtering applied
        # In a real app, we'd query full history. Here we use what's passed (filtered data).
        
        # Days with Spend
        dates = self.df['date_obj'].dt.date.unique()
        days_active = len(dates)
        
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")
        
        grid.add_row("Total Spent:", f"[bold green]${total:,.2f}[/bold green]")
        grid.add_row("Transactions:", str(count))
        grid.add_row("Daily Average:", f"${total/max(1, days_active):.2f}")
        grid.add_row("Active Days:", str(days_active))
        
        return grid

    def _generate_trends(self):
        # Weekly trends (simplified as daily grouping)
        daily = self.df.groupby(self.df['date_obj'].dt.date)['amount'].sum()
        
        # Sparkline logic using plotext?
        # Plotext prints to stdout, capturing it is tricky.
        # We can use simple ASCII bars manually for Rich.
        
        if daily.empty:
            return "No trend data."
            
        values = daily.tail(7).values # Last 7 active days
        if len(values) < 2:
            return "Need more data for trends."
            
        # Draw charts with plain text blocks
        blocks = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        # Normalize
        min_v, max_v = min(values), max(values)
        if max_v == min_v:
             normalized = [0 for _ in values]
        else:
             normalized = [int((v - min_v) / (max_v - min_v) * 7) for v in values]
             
        chart = "".join([blocks[n] for n in normalized])
        
        trend_text = f"Recent Activity: {chart}\n\n"
        
        # Week over Week
        # Find 'this week' vs 'last week' if data allows
        # For now, just show daily changes
        change = values[-1] - values[0]
        color = "red" if change > 0 else "green"
        trend_text += f"Change over period: [{color}]{change:+.2f}[/{color}]"
        
        return trend_text

    def _generate_categories(self):
        cats = self.df.groupby('category')['amount'].sum().sort_values(ascending=False).head(5)
        total = self.df['amount'].sum()
        
        table = Table.grid(expand=True)
        table.add_column()
        table.add_column(justify="right")
        table.add_column(justify="right")
        
        for cat, amt in cats.items():
            pct = (amt / total) * 100
            table.add_row(cat, f"${amt:.2f}", f"({pct:.1f}%)")
            
        return table

    def _generate_predictions(self):
        # Consistency Score (Simple std dev inverse)
        if len(self.df) > 5:
            std_dev = self.df['amount'].std()
            mean = self.df['amount'].mean()
            # Lower CV (std/mean) is better consistency
            cv = std_dev / mean if mean > 0 else 0
            score = max(0, min(100, int(100 * (1 - cv))))
            grade = "A" if score > 80 else "B" if score > 60 else "C" if score > 40 else "F"
        else:
            score = 0
            grade = "N/A"
            
        text = f"Consistency Score: [bold]{score}[/bold] ({grade})\n"
        
        # Projection: Daily avg * remaining days in month
        today = datetime.date.today()
        # Assume 30 days
        days_so_far = today.day
        daily_avg = self.df['amount'].sum() / max(1, days_so_far)
        remaining = 30 - days_so_far
        if remaining > 0:
            projected = daily_avg * remaining
            text += f"\nProj. Remaining: [yellow]${projected:.2f}[/yellow]"
            text += f"\nProj. Month Total: [bold]${(self.df['amount'].sum() + projected):.2f}[/bold]"
            
        return text

    def _generate_time_analysis(self):
        if self.df.empty: return "No data."
        
        # Day of Week
        self.df['dow'] = self.df['date_obj'].dt.day_name()
        dow_counts = self.df['dow'].value_counts()
        dow_sum = self.df.groupby('dow')['amount'].sum()
        
        busiest_day = dow_counts.idxmax() if not dow_counts.empty else "N/A"
        expensive_day = dow_sum.idxmax() if not dow_sum.empty else "N/A"
        
        text = f"Busiest Day: [bold cyan]{busiest_day}[/bold cyan] ({dow_counts.max()} txns)\n"
        text += f"Most Expensive Day: [bold red]{expensive_day}[/bold red] (${dow_sum.max():.2f})\n\n"
        
        # Hourly (if available)
        # self.df['hour'] = self.df['date_obj'].dt.hour
        # ... logic for hourly ...
        
        return text

    def run_command(self, basics=False, trends=False, categories=False, predict=False, time=False):
        if self.df.empty:
            console.print("[red]No data available for insights.[/red]")
            return

        if basics or (not trends and not categories and not predict and not time):
            console.print(self.get_dashboard())
            return
            
        # Specific modes
        if trends:
            console.print(Panel(self._generate_trends(), title="Trends Analysis"))
        if categories:
             console.print(Panel(self._generate_categories(), title="Category Analysis"))
        if predict:
             console.print(Panel(self._generate_predictions(), title="Predictive Analysis"))
        if time:
             console.print(Panel(self._generate_time_analysis(), title="Time Analysis"))
