from typing import List, Dict, Any
from datetime import datetime, timedelta

class DuplicateDetector:
    def __init__(self, existing_transactions: List[Dict]):
        self.existing = existing_transactions

    def is_duplicate(self, transaction: Any, tolerance_days: int = 1) -> bool:
        """
        Check if a transaction (likely an importer Transaction object or dict)
        is already in the existing data.
        
        Criteria:
        1. Same Amount (exact float match)
        2. Same Description (or very close)
        3. Date within tolerance
        """
        
        # Normalize incoming transaction data
        if hasattr(transaction, 'amount'):
            amt = transaction.amount
            desc = transaction.description
            date_str = transaction.date
        else:
            amt = transaction.get('amount')
            desc = transaction.get('note') or transaction.get('description')
            date_str = transaction.get('date') or transaction.get('timestamp')

        # Parse date
        try:
            target_date = datetime.fromisoformat(date_str)
        except:
             # Fallback parsing logic identical to base importer needed if not ISO
             return False # Can't compare dates safely

        for exist in self.existing:
            # Check Amount
            e_amt = exist.get('amount')
            if abs(e_amt - amt) > 0.01: # Float tolerance
                continue
                
            # Check Description
            # Simple inclusion checks or string equality
            # Existing uses 'note' usually? Or we store raw 'description' separately?
            # dot-spend currently uses 'note' for description.
            e_note = exist.get('note', '').upper()
            if desc.upper() not in e_note and e_note not in desc.upper():
                 # Maybe edit distance check later? For now, strict-ish match.
                 # If descriptions are totally different, probably not same tx.
                 continue

            # Check Date
            # Existing data has 'timestamp' (ISO)
            try:
                e_date = datetime.fromisoformat(exist.get('timestamp'))
                delta = abs((e_date - target_date).days)
                if delta <= tolerance_days:
                    return True
            except:
                continue
                
        return False
