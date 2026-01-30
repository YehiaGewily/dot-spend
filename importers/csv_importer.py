import pandas as pd
from typing import List, Dict, Optional
from .base import BaseImporter, Transaction

class CSVImporter(BaseImporter):
    def __init__(self):
        super().__init__()
        self.mapping = {} # Column mapping: {'date': 'Date', 'amount': 'Amount', ...}

    def set_mapping(self, mapping: Dict[str, str]):
        self.mapping = mapping

    def parse(self, file_path: str, **kwargs) -> List[Transaction]:
        """
        Parse CSV file using pandas.
        kwargs can include 'encoding', 'delimiter', 'skip_rows'.
        """
        encoding = kwargs.get('encoding', 'utf-8')
        delimiter = kwargs.get('delimiter', ',')
        skiprows = kwargs.get('skip_rows', 0)
        
        try:
            df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, skiprows=skiprows)
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}")

        # If mapping provided via kwargs, use it
        if 'mapping' in kwargs:
            self.set_mapping(kwargs['mapping'])

        # Validate mapping
        required_cols = ['date', 'amount', 'description'] # Internal names
        # Map internal -> CSV column name
        # We need to invert or direct map? 
        # Usually mapping is internal_field -> csv_column_name
        
        for field in required_cols:
            if field not in self.mapping:
                # Try auto-detect if not set?
                # For this implementation, we assume mapping is set or handled by caller (wizard)
                # But let's try a simple auto-detect if completely empty
                if not self.mapping:
                     self.mapping = self._auto_detect_columns(df.columns)
            
            if field not in self.mapping or self.mapping[field] not in df.columns:
                # If still missing, we can't proceed (or maybe we can if auto-detect worked partially?)
                # Actually, duplicate fields handling is tricky.
                pass 

        if not self.mapping:
             raise ValueError("Column mapping not configured.")

        transactions = []
        for _, row in df.iterrows():
            try:
                date_str = str(row[self.mapping['date']])
                amount_val = row[self.mapping['amount']]
                desc_str = str(row[self.mapping['description']])
                
                # Cleanup Amount
                if isinstance(amount_val, str):
                    amount_val = amount_val.replace('$', '').replace(',', '')
                    # Handle debit/credit indicators if needed (e.g. "100 CR")
                    # For now assume standard float-able string
                
                amount = float(amount_val)
                
                # Invert amount if needed (some banks show debits as positive, we want expenses negative? or positive?)
                # dot-spend likely treats expenses as positive numbers in input, or negative?
                # Let's check existing data model.
                # main.py: add command takes positive amount. 
                # Import usually brings negative numbers for expenses.
                # We should convert to positive for expenses? 
                # Let's check `add_expense` in `datastore.py`.
                # entry['amount'] = amount. So we store what we get.
                # Usually TUI shows positive.
                # If bank statement has -50.00 for grocery:
                # We want to store 50.00.
                if kwargs.get('invert_negative', False) and amount < 0:
                    amount = abs(amount)
                elif kwargs.get('invert_positive', False): # For credit card statements where 50.00 is a charge
                    pass # Keep as positive

                # Date parsing
                # user can pass 'date_format' in kwargs
                date_iso = self.normalize_date(date_str, kwargs.get('date_format'))

                transactions.append(Transaction(
                    date=date_iso,
                    amount=amount,
                    description=desc_str,
                    source=f"csv:{file_path}"
                ))
            except Exception as e:
                # Log error or skip?
                # Ideally we skip and report
                continue
                
        return transactions

    def _auto_detect_columns(self, columns: List[str]) -> Dict[str, str]:
        mapping = {}
        columns_lower = [c.lower() for c in columns]
        
        # Date
        for candidate in ['date', 'txn date', 'transaction date', 'posting date']:
            if candidate in columns_lower:
                mapping['date'] = columns[columns_lower.index(candidate)]
                break
        
        # Amount
        for candidate in ['amount', 'amt', 'value', 'transaction amount']:
            if candidate in columns_lower:
                mapping['amount'] = columns[columns_lower.index(candidate)]
                break
                
        # Description
        for candidate in ['description', 'desc', 'payee', 'merchant', 'narrative', 'transaction description']:
             if candidate in columns_lower:
                mapping['description'] = columns[columns_lower.index(candidate)]
                break
                
        return mapping
