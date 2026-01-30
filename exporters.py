import json
import csv
import pandas as pd
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

class ExportManager:
    def __init__(self, data):
        self.data = data
        self.df = pd.DataFrame(data)
        # Ensure consistent columns
        if not self.df.empty:
            # Reorder if possible
            cols = ["id", "date", "category", "note", "amount"]
            existing = [c for c in cols if c in self.df.columns]
            start_cols = existing
            other_cols = [c for c in self.df.columns if c not in cols and c != "timestamp"]
            self.df = self.df[start_cols + other_cols]

    def export(self, format: str, path: str, **kwargs):
        """
        Dispatch export to specific methods.
        """
        target_path = Path(path)
        if target_path.is_dir():
             # Auto-generate filename
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"expenses_{timestamp}.{format}"
            target_path = target_path / filename
            
        # Create parent dir if needed
        if not target_path.parent.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            progress.add_task(description=f"Exporting to {format.upper()}...", total=None)
            
            try:
                if format == "csv":
                    self._export_csv(target_path, **kwargs)
                elif format == "xlsx":
                    self._export_excel(target_path, **kwargs)
                elif format == "json":
                    self._export_json(target_path, **kwargs)
                elif format == "pdf":
                    self._export_pdf(target_path, **kwargs)
                else:
                    raise ValueError(f"Unknown format: {format}")
                    
                rprint(f"[bold green]✔ Export successful:[/bold green] {target_path}")
                return target_path
            except Exception as e:
                rprint(f"[bold red]✘ Export failed:[/bold red] {e}")
                return None

    def _filter_fields(self, fields: str = None):
        if fields:
            # Check validity
            req_fields = [f.strip() for f in fields.split(",")]
            valid_fields = [f for f in req_fields if f in self.df.columns]
            return self.df[valid_fields]
        return self.df

    def _export_csv(self, path: Path, delimiter: str = ",", fields: str = None, **kwargs):
        df = self._filter_fields(fields)
        
        # Add summary row?
        # Pandas to_csv doesn't natively do summary footer easily without appending
        # We can append a summary row to the DF temporarily
        if not df.empty and "amount" in df.columns:
            total = df["amount"].sum()
            avg = df["amount"].mean()
            count = len(df)
            
            # Create summary series
            summary = {c: "" for c in df.columns}
            if "id" in df.columns: summary["id"] = "TOTAL"
            if "category" in df.columns: summary["category"] = f"Count: {count}"
            if "amount" in df.columns: summary["amount"] = total
            
            # Use pd.concat instead of append (deprecated)
            summary_df = pd.DataFrame([summary])
            df = pd.concat([df, summary_df], ignore_index=True)
            
        df.to_csv(path, index=False, sep=delimiter)

    def _export_excel(self, path: Path, fields: str = None, **kwargs):
        df = self._filter_fields(fields)
        
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Expenses', index=False)
            
            # Access workbook for styling
            workbook = writer.book
            worksheet = writer.sheets['Expenses']
            
            # Auto-adjust columns
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
                
            # Freeze header
            worksheet.freeze_panes = worksheet['A2']
            
            # Summary Sheet
            if not df.empty and "category" in df.columns and "amount" in df.columns:
                summary = df.groupby("category")["amount"].sum().reset_index()
                summary.to_excel(writer, sheet_name='Summary', index=False)


    def _export_json(self, path: Path, fields: str = None, **kwargs):
        df = self._filter_fields(fields)
        # Standard json export
        df.to_json(path, orient="records", indent=4, date_format="iso")

    def _export_pdf(self, path: Path, template: str = "simple", fields: str = None, **kwargs):
        # Using ReportLab
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_text = f"Expense Report"
        elements.append(Paragraph(title_text, styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Summary stats
        if not self.df.empty:
            total = self.df["amount"].sum()
            count = len(self.df)
            summary_text = f"<b>Total Spent:</b> ${total:.2f} <br/> <b>Count:</b> {count} transactions"
            elements.append(Paragraph(summary_text, styles['Normal']))
            elements.append(Spacer(1, 24))
            
            # Chart
            if template == "detailed":
                # Generate pie chart
                cat_sum = self.df.groupby("category")["amount"].sum()
                if not cat_sum.empty:
                    plt.figure(figsize=(6, 4))
                    plt.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%')
                    plt.title("Spending by Category")
                    
                    img_buffer = BytesIO()
                    plt.savefig(img_buffer, format='png')
                    img_buffer.seek(0)
                    plt.close()
                    
                    im = Image(img_buffer, width=400, height=300)
                    elements.append(im)
                    elements.append(Spacer(1, 24))

        # Table
        df = self._filter_fields(fields)
        # Convert to list of lists including header
        if not df.empty:
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Basic Table Styling
            table = Table(data)
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            table.setStyle(style)
            elements.append(table)
        else:
             elements.append(Paragraph("No data available.", styles['Normal']))
            
        doc.build(elements)
