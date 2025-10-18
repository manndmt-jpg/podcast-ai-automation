#!/usr/bin/env python3
"""
Cleanup script to remove duplicate entries from Notion database.
Keeps the most recent entry for each Podcast+Episode combination.

Usage: python3 scripts/cleanup_notion_duplicates.py [--dry-run]
"""

import os
import sys
import argparse
from notion_client import Client
from collections import defaultdict
from datetime import datetime


def find_duplicates(client: Client, dbid: str):
    """Find all duplicate entries in the database"""
    print("🔍 Scanning Notion database for duplicates...")

    # Get all pages (handle pagination)
    all_pages = []
    has_more = True
    start_cursor = None

    while has_more:
        query_params = {
            "database_id": dbid,
            "page_size": 100,
        }
        if start_cursor:
            query_params["start_cursor"] = start_cursor

        results = client.databases.query(**query_params)
        all_pages.extend(results.get("results", []))

        has_more = results.get("has_more", False)
        start_cursor = results.get("next_cursor")

    print(f"   Found {len(all_pages)} total entries")

    # Group by podcast+episode
    episodes = defaultdict(list)

    for page in all_pages:
        props = page["properties"]

        # Extract podcast and episode
        podcast = props.get("Podcast", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
        episode = props.get("Episode", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")

        if not podcast or not episode:
            continue

        key = (podcast, episode)
        episodes[key].append({
            "id": page["id"],
            "created_time": page.get("created_time", ""),
            "last_edited_time": page.get("last_edited_time", ""),
        })

    # Find duplicates (more than 1 entry per podcast+episode)
    duplicates = {}
    for key, pages in episodes.items():
        if len(pages) > 1:
            # Sort by last_edited_time (most recent first)
            pages.sort(key=lambda x: x["last_edited_time"], reverse=True)
            duplicates[key] = pages

    return duplicates


def cleanup_duplicates(client: Client, duplicates: dict, dry_run: bool = True):
    """Remove duplicate entries, keeping the most recent one"""
    if not duplicates:
        print("✅ No duplicates found!")
        return

    print(f"\n📋 Found {len(duplicates)} episodes with duplicates:")
    print("=" * 80)

    total_to_delete = 0
    for (podcast, episode), pages in duplicates.items():
        print(f"\n{podcast} — {episode}")
        print(f"   {len(pages)} copies found:")
        for i, page in enumerate(pages):
            status = "KEEP (most recent)" if i == 0 else "DELETE"
            print(f"   [{status}] Created: {page['created_time'][:10]}, "
                  f"Edited: {page['last_edited_time'][:10]}, "
                  f"ID: {page['id']}")

        total_to_delete += len(pages) - 1

    print("\n" + "=" * 80)
    print(f"📊 Summary: {total_to_delete} duplicate entries to delete")

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes made")
        print("   Run with --execute to actually delete duplicates")
        return

    # Confirm deletion
    print("\n⚠️  WARNING: This will permanently delete the duplicate entries!")
    response = input("   Type 'DELETE' to confirm: ")

    if response != "DELETE":
        print("   Cancelled.")
        return

    # Delete duplicates
    print("\n🗑️  Deleting duplicates...")
    deleted_count = 0

    for (podcast, episode), pages in duplicates.items():
        # Skip the first (most recent) entry
        for page in pages[1:]:
            try:
                client.pages.update(
                    page_id=page["id"],
                    archived=True
                )
                deleted_count += 1
                print(f"   ✓ Deleted: {podcast[:30]} — {episode[:40]}")
            except Exception as e:
                print(f"   ✗ Failed to delete {page['id']}: {e}")

    print(f"\n✅ Cleanup complete! Deleted {deleted_count} duplicate entries.")


def main():
    parser = argparse.ArgumentParser(description="Cleanup duplicate Notion entries")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete duplicates (default is dry-run)"
    )
    args = parser.parse_args()

    # Get credentials
    token = os.getenv("NOTION_TOKEN")
    dbid = os.getenv("NOTION_DATABASE_ID")

    if not token or not dbid:
        print("❌ Error: NOTION_TOKEN and NOTION_DATABASE_ID must be set")
        sys.exit(1)

    client = Client(auth=token)

    # Find duplicates
    duplicates = find_duplicates(client, dbid)

    # Cleanup
    dry_run = not args.execute
    cleanup_duplicates(client, duplicates, dry_run=dry_run)


if __name__ == "__main__":
    main()
