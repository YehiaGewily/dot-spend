import re
from typing import List, Dict, Optional
from collections import Counter
import json
from pathlib import Path

# Try importing sklearn, but don't fail if missing
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    HAS_sklearn = True
except ImportError:
    HAS_sklearn = False

class RuleCategorizer:
    def __init__(self, rules_path: str = None):
        self.rules = []
        if rules_path and Path(rules_path).exists():
            with open(rules_path, 'r') as f:
                # Expecting JSON or YAML format rules
                # For simplicity, we'll start with JSON structure list
                try:
                    self.rules = json.load(f)
                except:
                    pass
        else:
            # Default rules
            self.rules = [
                {"pattern": "UBER|LYFT", "category": "Transport", "regex": True},
                {"pattern": "SAFEWAY|TRADER JOE|WHOLE FOODS", "category": "Groceries", "regex": True},
                {"pattern": "NETFLIX|SPOTIFY|HBO|DISNEY", "category": "Entertainment", "regex": True},
                {"pattern": "AMAZON|EBAY", "category": "Shopping", "regex": True},
                {"pattern": "PG&E|EVERSOURCE|SCE", "category": "Utilities", "regex": True},
                {"pattern": "STARBUCKS|COFFEE|CAFE|PEET'S", "category": "Dining", "regex": True},
                {"pattern": "RESTAURANT|DINER|PIZZA|BURGER|SUSHI", "category": "Dining", "regex": True},
            ]

    def categorize(self, description: str, amount: float = 0) -> Optional[str]:
        desc_upper = description.upper()
        
        for rule in self.rules:
            pattern = rule.get("pattern", "").upper()
            is_regex = rule.get("regex", False)
            category = rule.get("category")
            
            # Simple amount check if rule has it
            min_amt = rule.get("min_amount")
            max_amt = rule.get("max_amount")
            if min_amt is not None and amount < min_amt: continue
            if max_amt is not None and amount > max_amt: continue
            
            if is_regex:
                if re.search(pattern, desc_upper):
                    return category
            else:
                if pattern in desc_upper:
                    return category
                    
        return None

class MLCategorizer:
    def __init__(self):
        self.model = None
        self.is_trained = False

    def train(self, transactions: List[Dict]):
        """
        Train the model on a list of existing transactions.
        Transactions should be dicts with 'note'/'description' and 'category'.
        """
        if not HAS_sklearn:
            return

        descriptions = []
        categories = []
        
        for tx in transactions:
            # Prefer 'note' as description, fallback to nothing
            desc = tx.get('note') or tx.get('description', '')
            cat = tx.get('category')
            if desc and cat:
                descriptions.append(desc)
                categories.append(cat)
        
        if len(descriptions) < 10: # Minimum data to bother training
            return

        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english', max_features=1000)),
            ('clf', LogisticRegression(random_state=42))
        ])
        
        try:
            self.model.fit(descriptions, categories)
            self.is_trained = True
        except Exception:
            self.is_trained = False

    def predict(self, description: str) -> Optional[str]:
        if not self.is_trained or not self.model:
            return None
        try:
            return self.model.predict([description])[0]
        except:
            return None
