from datetime import datetime, timedelta, timezone

def create_expiry_timestamp(hours: int) -> str:
    """
    Create a UTC expiry timestamp after given hours and return ISO string.
    """
    expiry = datetime.now(timezone.utc) + timedelta(hours=hours)
    return expiry.isoformat()

def is_expired(expiry_time_str: str) -> bool:
    """
    Check if expiry timestamp (ISO string) is expired.
    """
    if not expiry_time_str:
        return True
    expiry = datetime.fromisoformat(expiry_time_str)
    return datetime.now(timezone.utc) > expiry

def remaining_time(expiry_time_str: str):
    """
    Get remaining time until expiry as timedelta.
    """
    if not expiry_time_str:
        return timedelta(seconds=0)
    expiry = datetime.fromisoformat(expiry_time_str)
    return expiry - datetime.now(timezone.utc)
