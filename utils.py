import datetime
from typing import Tuple, Optional, List
import dateutil.parser

def parse_date(date_str: str) -> datetime.datetime:
    """Parses a string into a datetime object. Returns None on failure."""
    try:
        # Try standard ISO first
        return datetime.datetime.fromisoformat(date_str)
    except ValueError:
        pass
    
    try:
        # Flexible parsing
        return dateutil.parser.parse(date_str)
    except (ValueError, TypeError):
        return None

def get_date_range(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: Optional[int] = None,
    today: bool = False,
    yesterday: bool = False,
    this_week: bool = False,
    last_week: bool = False,
    this_month: bool = False,
    last_month: bool = False,
    this_year: bool = False
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """
    Returns (start_date, end_date) based on flags.
    Dates are returned as 'start of day' and 'end of day' appropriately.
    """
    now = datetime.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start = None
    end = None

    if today:
        start = today_start
        end = now
    elif yesterday:
        start = today_start - datetime.timedelta(days=1)
        end = today_start - datetime.timedelta(seconds=1)
    elif days:
        start = today_start - datetime.timedelta(days=days)
        end = now
    elif this_week:
        # Monday = 0
        start = today_start - datetime.timedelta(days=today_start.weekday())
        end = now
    elif last_week:
        current_monday = today_start - datetime.timedelta(days=today_start.weekday())
        start = current_monday - datetime.timedelta(weeks=1)
        end = current_monday - datetime.timedelta(seconds=1)
    elif this_month:
        start = today_start.replace(day=1)
        end = now
    elif last_month:
        this_month_start = today_start.replace(day=1)
        end = this_month_start - datetime.timedelta(seconds=1)
        start = end.replace(day=1, hour=0, minute=0, second=0)
    elif this_year:
        start = today_start.replace(month=1, day=1)
        end = now
    
    # Explicit overrides take precedence
    if from_date:
        parsed = parse_date(from_date)
        if parsed:
            start = parsed.replace(hour=0, minute=0, second=0)
    
    if to_date:
        parsed = parse_date(to_date)
        if parsed:
            end = parsed.replace(hour=23, minute=59, second=59)

    return start, end

def filter_data_by_date(data: List[dict], start: Optional[datetime.datetime], end: Optional[datetime.datetime]) -> List[dict]:
    """Filters the list of expense dictionaries by date range."""
    if not start and not end:
        return data
        
    filtered = []
    for item in data:
        try:
            # We assume item['date'] is the ISO string or parseable
            # In our main.py we will standardize on 'timestamp' (ISO)
            item_dt = parse_date(item.get('timestamp', item.get('date')))
            
            if not item_dt:
                continue
                
            # If item_dt is naive, assume local? Or should we enforce timezone awareness?
            # For simplicity in this CLI, we'll try to compare naively if possible
            # But parse_date might return aware if string had tz.
            # Let's strip tz for comparison to keep it simple locally
            item_dt = item_dt.replace(tzinfo=None)
            
            if start and item_dt < start:
                continue
            if end and item_dt > end:
                continue
                
            filtered.append(item)
        except Exception:
            continue
            
    return filtered
