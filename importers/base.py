from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    date: str  # ISO format YYYY-MM-DD (or with time)
    amount: float
    description: str
    category: str = None
    note: str = ""
    source: str = "" # e.g. "csv:statement.csv"

class BaseImporter(ABC):
    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> List[Transaction]:
        """
        Parse a file and return a list of Transaction objects.
        """
        pass
        
    def normalize_date(self, date_str: str, date_format: str = None) -> str:
        """Helper to convert various date strings to ISO format."""
        # This can be used by subclasses
        from dateutil import parser
        try:
            if date_format:
                dt = datetime.strptime(date_str, date_format)
            else:
                dt = parser.parse(date_str)
            return dt.isoformat()
        except Exception as e:
            # Fallback or re-raise
            raise ValueError(f"Could not parse date: {date_str}") from e
