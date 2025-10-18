"""
Date utilities for podcast pipeline
Ensures all dates are in ISO 8601 format compatible with Notion
"""

from datetime import datetime
import re


def to_iso_date(date_input: str) -> str:
    """
    Convert various date formats to ISO 8601 date format (YYYY-MM-DD).

    Supports:
    - ISO 8601 datetime: "2025-08-21T05:00:00+00:00" -> "2025-08-21"
    - ISO 8601 date: "2025-08-21" -> "2025-08-21"
    - YYYYMMDD: "20250821" -> "2025-08-21"
    - RFC 822: "Thu, 21 Aug 2025 05:00:00 -0000" -> "2025-08-21"

    Args:
        date_input: Date string in various formats

    Returns:
        ISO 8601 date string (YYYY-MM-DD)

    Raises:
        ValueError: If date format is not recognized
    """
    if not date_input:
        return ""

    date_input = date_input.strip()

    # Already ISO date format (YYYY-MM-DD)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_input):
        return date_input

    # ISO datetime format (extract date part)
    # Must start with YYYY-MM-DD and contain T
    if re.match(r'^\d{4}-\d{2}-\d{2}T', date_input):
        return date_input.split('T')[0]

    # YYYYMMDD format
    if re.match(r'^\d{8}$', date_input):
        return f"{date_input[:4]}-{date_input[4:6]}-{date_input[6:8]}"

    # RFC 822 format (e.g., "Thu, 21 Aug 2025 05:00:00 -0000")
    # Try common RFC 822 patterns
    for fmt in [
        '%a, %d %b %Y %H:%M:%S %z',  # With timezone
        '%a, %d %b %Y %H:%M:%S',      # Without timezone
        '%d %b %Y %H:%M:%S %z',       # Without day name
        '%d %b %Y %H:%M:%S',          # Minimal
    ]:
        try:
            dt = datetime.strptime(date_input, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # If all else fails, raise error
    raise ValueError(f"Unrecognized date format: {date_input}")


def format_youtube_date(yyyymmdd: str) -> str:
    """
    Convert YouTube YYYYMMDD format to ISO date.
    Wrapper for backwards compatibility.

    Args:
        yyyymmdd: Date in YYYYMMDD format

    Returns:
        ISO 8601 date string (YYYY-MM-DD)
    """
    return to_iso_date(yyyymmdd)
