"""Multi-currency support with exchange rate handling."""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from config import DATA_DIR

CURRENCY_FILE = DATA_DIR / "currency.json"
RATES_FILE = DATA_DIR / "exchange_rates.json"

# Free API - no key required (limited requests)
EXCHANGE_API = "https://api.exchangerate-api.com/v4/latest/"

SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY",
    "INR", "MXN", "BRL", "KRW", "SGD", "HKD", "NOK", "SEK",
    "DKK", "NZD", "ZAR", "RUB", "TRY", "PLN", "THB", "MYR"
]

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$",
    "AUD": "A$", "CHF": "Fr", "CNY": "¥", "INR": "₹", "MXN": "$",
    "BRL": "R$", "KRW": "₩", "SGD": "S$", "HKD": "HK$", "NOK": "kr",
    "SEK": "kr", "DKK": "kr", "NZD": "NZ$", "ZAR": "R", "RUB": "₽",
    "TRY": "₺", "PLN": "zł", "THB": "฿", "MYR": "RM"
}

class CurrencyManager:
    def __init__(self):
        self.config = self._load_config()
        self.rates = self._load_rates()
    
    def _load_config(self) -> Dict:
        if CURRENCY_FILE.exists():
            with open(CURRENCY_FILE) as f:
                return json.load(f)
        return {"base": "USD", "auto_convert": True, "last_update": None}
    
    def _save_config(self):
        with open(CURRENCY_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def _load_rates(self) -> Dict:
        if RATES_FILE.exists():
            with open(RATES_FILE) as f:
                return json.load(f)
        return {"base": "USD", "rates": {"USD": 1.0}, "date": None}
    
    def _save_rates(self):
        with open(RATES_FILE, "w") as f:
            json.dump(self.rates, f, indent=2)
    
    @property
    def base_currency(self) -> str:
        return self.config.get("base", "USD")
    
    def set_base(self, currency: str) -> bool:
        currency = currency.upper()
        if currency not in SUPPORTED_CURRENCIES:
            return False
        self.config["base"] = currency
        self._save_config()
        return True
    
    def update_rates(self) -> bool:
        """Fetch latest exchange rates from API."""
        try:
            response = requests.get(f"{EXCHANGE_API}{self.base_currency}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.rates = {
                    "base": data["base"],
                    "rates": data["rates"],
                    "date": datetime.now().isoformat()
                }
                self._save_rates()
                self.config["last_update"] = datetime.now().isoformat()
                self._save_config()
                return True
        except Exception as e:
            print(f"Failed to fetch rates: {e}")
        return False
    
    def get_rate(self, from_currency: str, to_currency: str = None) -> float:
        """Get exchange rate between currencies."""
        if to_currency is None:
            to_currency = self.base_currency
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        rates = self.rates.get("rates", {})
        
        # If base matches, direct lookup
        if self.rates.get("base") == from_currency:
            return rates.get(to_currency, 1.0)
        
        # Cross rate calculation
        from_rate = rates.get(from_currency, 1.0)
        to_rate = rates.get(to_currency, 1.0)
        
        if from_rate == 0:
            return 1.0
        
        return to_rate / from_rate
    
    def convert(self, amount: float, from_currency: str, to_currency: str = None) -> float:
        """Convert amount between currencies."""
        rate = self.get_rate(from_currency, to_currency)
        return amount * rate
    
    def format_amount(self, amount: float, currency: str = None) -> str:
        """Format amount with currency symbol."""
        if currency is None:
            currency = self.base_currency
        symbol = CURRENCY_SYMBOLS.get(currency.upper(), currency)
        return f"{symbol}{amount:.2f}"
    
    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if rates are older than max_age_hours."""
        last_update = self.config.get("last_update")
        if not last_update:
            return True
        
        try:
            update_time = datetime.fromisoformat(last_update)
            return datetime.now() - update_time > timedelta(hours=max_age_hours)
        except:
            return True
