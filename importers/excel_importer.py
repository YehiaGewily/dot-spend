import pandas as pd
from typing import List, Dict, Optional
from .base import BaseImporter, Transaction
from .csv_importer import CSVImporter

class ExcelImporter(CSVImporter):
    """
    Excel importer behaves effectively like CSV importer but reads XLSX.
    Inherits from CSVImporter to reuse mapping logic.
    """
    def parse(self, file_path: str, **kwargs) -> List[Transaction]:
        sheet_name = kwargs.get('sheet_name', 0) # Default to first sheet
        skiprows = kwargs.get('skip_rows', 0)
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")

        # Reuse CSV logic
        # But we need to make sure self.mapping is handled.
        
        # Manually invoke similar logic since we can't just call CSVImporter.parse directly 
        # because it calls read_csv. We have the df now.
        
        if 'mapping' in kwargs:
            self.set_mapping(kwargs['mapping'])
            
        if not self.mapping:
             self.mapping = self._auto_detect_columns(df.columns)
             
        # ... logic validation ... (simplified repeat for now)
        transactions = []
        for _, row in df.iterrows():
            try:
                date_str = str(row[self.mapping['date']])
                amount_val = row[self.mapping['amount']]
                desc_str = str(row[self.mapping['description']])
                
                amount = float(amount_val)
                if kwargs.get('invert_negative', False) and amount < 0:
                    amount = abs(amount)

                date_iso = self.normalize_date(date_str, kwargs.get('date_format'))

                transactions.append(Transaction(
                    date=date_iso,
                    amount=amount,
                    description=desc_str,
                    source=f"xlsx:{file_path}"
                ))
            except:
                continue
                
        return transactions
