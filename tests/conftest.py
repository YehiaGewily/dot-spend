import pytest
import json
import tempfile
from pathlib import Path

@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "dot-spend"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_expenses():
    """Sample expense data for testing."""
    return [
        {"id": "abc123", "amount": 25.00, "category": "Food", "note": "Lunch", "timestamp": "2024-01-15T12:00:00"},
        {"id": "def456", "amount": 50.00, "category": "Transport", "note": "Uber", "timestamp": "2024-01-15T14:00:00"},
        {"id": "ghi789", "amount": 100.00, "category": "Shopping", "note": "Clothes", "timestamp": "2024-01-16T10:00:00"},
    ]

@pytest.fixture
def expenses_file(tmp_data_dir, sample_expenses):
    """Create a temp expenses.json file."""
    file_path = tmp_data_dir / "expenses.json"
    with open(file_path, "w") as f:
        json.dump(sample_expenses, f)
    return file_path
