# Notion Duplicate Fix Summary

## Problem Identified
The Notion integration was creating duplicate pages for the same episodes. Investigation revealed:
- **Root cause**: `push_to_notion.py` always created new pages without checking if they already existed
- **Impact**: 9 episodes had duplicates (11 duplicate entries total)
- **Date range**: Duplicates from Sept 22 - Oct 17, 2025

## Solution Implemented

### 1. Added Duplicate Prevention (scripts/push_to_notion.py)
Modified the push_to_notion script with three key changes:

**a) Added duplicate detection function:**
```python
def find_existing_page(client, dbid, podcast, episode):
    """Query Notion database to check if page already exists"""
    # Searches for exact match on Podcast+Episode properties
    # Returns page ID if found, None otherwise
```

**b) Added update function:**
```python
def update_with_batches(client, page_id, properties, blocks):
    """Update existing page properties and replace content"""
    # Updates properties and replaces all content blocks
```

**c) Modified main logic:**
- Now checks for existing pages before creating new ones
- Updates existing pages instead of creating duplicates
- Shows "♻️ Updated existing Notion page" message for updates
- Shows "✅ Created Notion page" message for new entries

### 2. Created Cleanup Script (scripts/cleanup_notion_duplicates.py)
New utility script to remove existing duplicates:
- Scans entire Notion database for duplicates
- Groups by Podcast+Episode combination
- Keeps the most recently edited version
- Archives older duplicates
- Includes dry-run mode for safety

## Testing Results

✅ **Duplicate Prevention Tested:**
- Ran push_to_notion.py on existing episodes
- Successfully updated instead of creating duplicates
- Confirmed with "♻️ Updated existing Notion page" messages

✅ **Cleanup Script Tested:**
- Found 11 duplicate entries across 9 episodes
- Dry-run mode shows what will be deleted
- Ready to execute with `--execute` flag

## Episodes with Duplicates Found

1. **a16z Podcast** — Dylan Patel on the AI Chip Race (2 copies)
2. **a16z Podcast** — From Vibe Coding to Vibe Researching (2 copies)
3. **The Diary of a CEO** — Louis Tomlinson (3 copies)
4. **No Priors** — Humans&: Bridging IQ and EQ (2 copies)
5. **Lenny's Podcast** — First interview with Scale AI's CEO (2 copies)
6. **The Diary of a CEO** — Neil deGrasse Tyson (2 copies)
7. **The Diary of a CEO** — Women's Fertility & Lifestyle Debate (2 copies)
8. **Latent Space** — Why Fine-Tuning Lost and RL Won (3 copies)
9. **a16z Podcast** — Keith Rabois (2 copies)

## Next Steps

### To Clean Up Existing Duplicates:

```bash
# 1. Review what will be deleted (dry-run mode)
cd ~/podcast_summary_project
python3 scripts/cleanup_notion_duplicates.py

# 2. Execute the cleanup (requires typing 'DELETE' to confirm)
python3 scripts/cleanup_notion_duplicates.py --execute
```

### Going Forward:
- ✅ Duplicate prevention is now active in the pipeline
- ✅ All future episodes will update existing pages if they exist
- ✅ Cron jobs will automatically use the updated logic
- 🔧 Run cleanup script once to remove existing duplicates

## Technical Details

**Modified files:**
- `scripts/push_to_notion.py` - Added duplicate detection and update logic

**New files:**
- `scripts/cleanup_notion_duplicates.py` - Utility to clean existing duplicates
- `DUPLICATE_FIX_SUMMARY.md` - This document

**How duplicate detection works:**
1. Before creating a page, query Notion database
2. Search for exact match on `Podcast` + `Episode` properties
3. If found: Update existing page
4. If not found: Create new page

**Why duplicates occurred:**
- The original script always created new pages
- If the pipeline ran multiple times for the same episode, it created duplicates
- The `seen.json` tracking prevented re-processing, but didn't prevent duplicate Notion entries
- This could happen during testing, manual runs, or if seen.json was cleared

## Status: ✅ FIXED
- Duplicate prevention: **Active**
- Cleanup script: **Ready to run**
- Future duplicates: **Prevented**
