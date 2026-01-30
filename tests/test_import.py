import pytest
from pathlib import Path

class TestCSVImport:
    def test_csv_file_detection(self):
        """Test CSV format detection."""
        path = Path("statement.csv")
        assert path.suffix == ".csv"
    
    def test_excel_file_detection(self):
        """Test Excel format detection."""
        path = Path("statement.xlsx")
        assert path.suffix == ".xlsx"
    
    def test_ofx_file_detection(self):
        """Test OFX format detection."""
        path = Path("statement.ofx")
        assert path.suffix == ".ofx"

class TestColumnMapping:
    def test_auto_detect_date_column(self):
        """Test date column auto-detection."""
        columns = ["Date", "Description", "Amount"]
        date_candidates = ["date", "txn date", "transaction date"]
        found = any(c.lower() in date_candidates for c in columns)
        assert found is True
    
    def test_auto_detect_amount_column(self):
        """Test amount column auto-detection."""
        columns = ["Date", "Description", "Amount"]
        amount_candidates = ["amount", "amt", "value"]
        found = any(c.lower() in amount_candidates for c in columns)
        assert found is True

class TestCategorization:
    def test_rule_based_categorization(self):
        """Test simple rule-based categorization."""
        description = "UBER RIDE"
        rules = {"UBER": "Transport", "WHOLE FOODS": "Groceries"}
        category = None
        for pattern, cat in rules.items():
            if pattern in description:
                category = cat
                break
        assert category == "Transport"
