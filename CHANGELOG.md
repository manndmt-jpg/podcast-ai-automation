# Changelog

## 2025-10-08 - Date Format Standardization

### Fixed
- **Notion date format compatibility**: All dates are now normalized to ISO 8601 date format (YYYY-MM-DD)
- **Date parsing utility**: Created centralized `utils/date_utils.py` to handle multiple date formats:
  - ISO 8601 datetime: `2025-08-21T05:00:00+00:00` → `2025-08-21`
  - ISO 8601 date: `2025-08-21` → `2025-08-21` (unchanged)
  - YYYYMMDD: `20250821` → `2025-08-21`
  - RFC 822: `Thu, 21 Aug 2025 05:00:00 -0000` → `2025-08-21`

### Changed
- **RSS Pipeline** (`automation/pipeline.py`): Now uses `to_iso_date()` to normalize published dates
- **YouTube Pipeline** (`automation/youtube_pipeline.py`): Replaced custom `format_youtube_date()` with centralized `to_iso_date()` utility
- **Metadata files**: All `.meta.json` files now contain dates in YYYY-MM-DD format compatible with Notion

### Technical Details
- Previous issue: Notion API requires ISO 8601 format for date properties
- RSS feeds return ISO datetime with timezone (e.g., `2025-10-06T05:00:00+00:00`)
- YouTube metadata returns YYYYMMDD format (e.g., `20250821`)
- Some RSS feeds may return RFC 822 format (e.g., `Thu, 21 Aug 2025 05:00:00 -0000`)
- Solution: All formats now normalized to `YYYY-MM-DD` before saving to metadata and pushing to Notion

### Testing
All date formats tested and verified:
```python
from utils.date_utils import to_iso_date

to_iso_date('2025-08-21T05:00:00+00:00')  # → '2025-08-21'
to_iso_date('2025-08-21')                  # → '2025-08-21'
to_iso_date('20250821')                    # → '2025-08-21'
to_iso_date('Thu, 21 Aug 2025 05:00:00 -0000')  # → '2025-08-21'
```

### Impact
- No action required for existing episodes
- Future episodes will automatically have correctly formatted dates
- Notion integration will work reliably without date parsing errors
