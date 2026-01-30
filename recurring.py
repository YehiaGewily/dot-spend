"""Recurring expenses management."""
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from config import DATA_DIR

RECURRING_FILE = DATA_DIR / "recurring.json"

class RecurringManager:
    def __init__(self):
        self.recurring = self._load()
    
    def _load(self) -> Dict:
        if RECURRING_FILE.exists():
            with open(RECURRING_FILE) as f:
                return json.load(f)
        return {}
    
    def _save(self):
        with open(RECURRING_FILE, "w") as f:
            json.dump(self.recurring, f, indent=2)
    
    def add(self, amount: float, category: str, note: str = "",
            frequency: str = "monthly", day: int = 1,
            start_date: str = None, end_date: str = None) -> str:
        """Add a recurring expense."""
        rec_id = str(uuid.uuid4())[:8]
        
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        self.recurring[rec_id] = {
            "amount": amount,
            "category": category,
            "note": note,
            "frequency": frequency,
            "day": day,
            "start_date": start_date,
            "end_date": end_date,
            "last_generated": None,
            "active": True
        }
        self._save()
        return rec_id
    
    def list_all(self) -> List[tuple]:
        """Return list of (id, data) tuples."""
        return [(k, v) for k, v in self.recurring.items()]
    
    def delete(self, rec_id: str) -> bool:
        if rec_id in self.recurring:
            del self.recurring[rec_id]
            self._save()
            return True
        return False
    
    def pause(self, rec_id: str) -> bool:
        if rec_id in self.recurring:
            self.recurring[rec_id]["active"] = False
            self._save()
            return True
        return False
    
    def resume(self, rec_id: str) -> bool:
        if rec_id in self.recurring:
            self.recurring[rec_id]["active"] = True
            self._save()
            return True
        return False
    
    def get_next_occurrence(self, rec: Dict, after_date: datetime) -> Optional[datetime]:
        """Calculate next occurrence after a given date."""
        freq = rec["frequency"]
        day = rec["day"]
        
        if freq == "daily":
            return after_date + timedelta(days=1)
        elif freq == "weekly":
            # day = 0-6 (Mon-Sun)
            days_ahead = day - after_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return after_date + timedelta(days=days_ahead)
        elif freq == "monthly":
            # Handle month-end edge cases
            next_month = after_date.month + 1 if after_date.month < 12 else 1
            next_year = after_date.year if after_date.month < 12 else after_date.year + 1
            
            # Clamp day to valid range for month
            import calendar
            max_day = calendar.monthrange(next_year, next_month)[1]
            actual_day = min(day, max_day)
            
            return datetime(next_year, next_month, actual_day)
        elif freq == "yearly":
            return datetime(after_date.year + 1, after_date.month, day)
        
        return None
    
    def sync_generate(self, add_expense_func) -> List[Dict]:
        """Generate missing recurring expenses."""
        generated = []
        today = datetime.now()
        
        for rec_id, rec in self.recurring.items():
            if not rec["active"]:
                continue
            
            # Check end date
            if rec["end_date"]:
                end = datetime.strptime(rec["end_date"], "%Y-%m-%d")
                if today > end:
                    continue
            
            # Determine last generated date
            if rec["last_generated"]:
                last = datetime.strptime(rec["last_generated"], "%Y-%m-%d")
            else:
                last = datetime.strptime(rec["start_date"], "%Y-%m-%d") - timedelta(days=1)
            
            # Generate all missing occurrences
            current = last
            while True:
                next_occ = self.get_next_occurrence(rec, current)
                if not next_occ or next_occ > today:
                    break
                
                # Add expense
                expense = add_expense_func(
                    amount=rec["amount"],
                    category=rec["category"],
                    note=f"{rec['note']} (Recurring)",
                    timestamp=next_occ.isoformat()
                )
                generated.append(expense)
                
                # Update last generated
                rec["last_generated"] = next_occ.strftime("%Y-%m-%d")
                current = next_occ
        
        self._save()
        return generated
    
    def forecast(self, months: int = 1) -> float:
        """Forecast total recurring costs for next N months."""
        total = 0.0
        for rec in self.recurring.values():
            if not rec["active"]:
                continue
            
            freq = rec["frequency"]
            amt = rec["amount"]
            
            if freq == "daily":
                total += amt * 30 * months
            elif freq == "weekly":
                total += amt * 4 * months
            elif freq == "monthly":
                total += amt * months
            elif freq == "yearly":
                total += amt * months / 12
        
        return total
