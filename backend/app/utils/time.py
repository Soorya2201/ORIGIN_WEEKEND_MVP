"""Time utility functions."""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """Parse ISO date string to datetime."""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


def format_iso_date(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()
