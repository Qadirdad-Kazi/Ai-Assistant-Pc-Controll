from datetime import datetime, timedelta

def _parse_date(date_str: str) -> str:
    """Parse date string to YYYY-MM-DD format."""
    print(f"Parsing: '{date_str}'")
    date_str = date_str.lower().strip()
    today = datetime.now()
    
    if date_str in ("today", ""):
        return today.strftime("%Y-%m-%d")
    elif date_str == "tomorrow":
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Day names
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        if day in date_str:
            current_day = today.weekday()
            days_ahead = i - current_day
            if days_ahead <= 0:
                days_ahead += 7
            if "next" in date_str:
                days_ahead += 7
            target = today + timedelta(days=days_ahead)
            return target.strftime("%Y-%m-%d")
    
    return today.strftime("%Y-%m-%d")

# Tests
print(f"Today: {_parse_date('today')}")
print(f"Tomorrow: {_parse_date('tomorrow')}")
print(f"Explicit Date (Should fail in current impl): {_parse_date('2025-12-25')}")
