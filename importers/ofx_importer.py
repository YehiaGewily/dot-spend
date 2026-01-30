from typing import List, Dict
from .base import BaseImporter, Transaction
from ofxparse import OfxParser

class OFXImporter(BaseImporter):
    def parse(self, file_path: str, **kwargs) -> List[Transaction]:
        try:
            with open(file_path, 'rb') as f:
                ofx = OfxParser.parse(f)
        except Exception as e:
            raise ValueError(f"Failed to parse OFX file: {e}")

        transactions = []
        if not ofx.account or not ofx.account.statement or not ofx.account.statement.transactions:
            return []

        for tx in ofx.account.statement.transactions:
            # tx.date is usually a datetime object already
            date_iso = tx.date.isoformat()
            
            # OFX amount is typically signed correctly (- for debit)
            # dot-spend generally uses positive for expenses in input, but we might want to standardize
            # For now, let's keep the raw amount or let user configure inversion
            amount = float(tx.amount)
            if kwargs.get('invert_negative', False) and amount < 0:
                amount = abs(amount)

            # OFX has payeepID, name, memo
            desc = tx.payee or tx.name or tx.memo or "Unknown"

            transactions.append(Transaction(
                date=date_iso,
                amount=amount,
                description=desc,
                source=f"ofx:{file_path}"
            ))
            
        return transactions
