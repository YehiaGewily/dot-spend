import pytest
import json
from pathlib import Path

class TestExpenseOperations:
    def test_sample_expenses_fixture(self, sample_expenses):
        """Test that sample expenses fixture works."""
        assert len(sample_expenses) == 3
        assert sample_expenses[0]["category"] == "Food"
    
    def test_expense_has_required_fields(self, sample_expenses):
        """Test expense structure."""
        required_fields = ["id", "amount", "category", "timestamp"]
        for expense in sample_expenses:
            for field in required_fields:
                assert field in expense
    
    def test_expenses_file_creation(self, expenses_file):
        """Test expenses file is created correctly."""
        assert expenses_file.exists()
        with open(expenses_file) as f:
            data = json.load(f)
        assert len(data) == 3
    
    def test_expense_amount_positive(self, sample_expenses):
        """Test all amounts are positive."""
        for expense in sample_expenses:
            assert expense["amount"] > 0

class TestDataValidation:
    def test_valid_category(self, sample_expenses):
        """Test categories are non-empty strings."""
        for expense in sample_expenses:
            assert isinstance(expense["category"], str)
            assert len(expense["category"]) > 0
    
    def test_valid_timestamp(self, sample_expenses):
        """Test timestamps are ISO format."""
        for expense in sample_expenses:
            assert "T" in expense["timestamp"]
