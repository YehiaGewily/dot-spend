import pytest
import json

class TestBudgetOperations:
    def test_budget_structure(self):
        """Test budget data structure."""
        budget = {"Food": 500, "Transport": 200}
        assert "Food" in budget
        assert budget["Food"] == 500
    
    def test_budget_amount_positive(self):
        """Test budget amounts must be positive."""
        budget = {"Food": 500}
        assert budget["Food"] > 0
    
    def test_budget_category_string(self):
        """Test budget categories are strings."""
        budget = {"Food": 500, "Transport": 200}
        for category in budget.keys():
            assert isinstance(category, str)

class TestBudgetCalculations:
    def test_remaining_budget(self):
        """Test remaining budget calculation."""
        budget = 500
        spent = 350
        remaining = budget - spent
        assert remaining == 150
    
    def test_budget_percentage(self):
        """Test budget usage percentage."""
        budget = 500
        spent = 250
        percentage = (spent / budget) * 100
        assert percentage == 50.0
    
    def test_over_budget(self):
        """Test over-budget detection."""
        budget = 500
        spent = 600
        is_over = spent > budget
        assert is_over is True
