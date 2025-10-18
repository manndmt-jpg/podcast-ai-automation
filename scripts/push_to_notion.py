# scripts/push_to_notion.py
import os
import sys
import json
import argparse
from typing import List, Dict
from notion_client import Client

MAX_CHARS = 1800   # safe rich_text size
BATCH_SIZE = 80    # children per request (API soft cap ~100)

# ---------- bold-safe chunking and inline markdown ----------

def _safe_chunks_preserving_bold(s: str, n: int):
    """
    Yield chunks <= n without splitting inside **bold** spans.
    Tries to break on spaces. If a chunk ends with an odd number
    of '**', extend to the next '**'.
    """
    i = 0
    while i < len(s):
        end = min(i + n, len(s))
        j = end
        # avoid mid-word split if possible
        if end < len(s) and not s[end].isspace():
            k = s.rfind(" ", i, end)
            if k > i + int(n * 0.6):
                j = k
        if j == i:
            j = end

        chunk = s[i:j]
        # make sure we do not leave bold unclosed in this chunk
        if chunk.count("**") % 2 == 1:
            nxt = s.find("**", j)
            if nxt != -1:
                j = min(nxt + 2, len(s))
                chunk = s[i:j]
            else:
                j = len(s)
                chunk = s[i:j]

        yield chunk
        i = j

def md_inline_to_rich(text: str):
    """
    Convert **bold** to Notion annotations.
    Assumes chunks do not split a bold span.
    """
    parts = text.split("**")
    if len(parts) == 1:
        return [{
            "type": "text",
            "text": {"content": text},
            "annotations": {"bold": False, "italic": False, "strikethrough": False,
                            "underline": False, "code": False, "color": "default"}
        }]
    rich = []
    for idx, seg in enumerate(parts):
        if seg == "":
            continue
        is_bold = (idx % 2 == 1)
        rich.append({
            "type": "text",
            "text": {"content": seg},
            "annotations": {"bold": is_bold, "italic": False, "strikethrough": False,
                            "underline": False, "code": False, "color": "default"}
        })
    return rich or [{
        "type": "text",
        "text": {"content": text},
        "annotations": {"bold": False, "italic": False, "strikethrough": False,
                        "underline": False, "code": False, "color": "default"}
    }]

# ---------- blocks ----------

def paragraph_blocks(text: str) -> List[Dict]:
    blocks = []
    for piece in _safe_chunks_preserving_bold(text, MAX_CHARS):
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": md_inline_to_rich(piece)}
        })
    return blocks

def bullet_blocks(text: str) -> List[Dict]:
    pieces = list(_safe_chunks_preserving_bold(text, MAX_CHARS))
    first = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": md_inline_to_rich(pieces[0])}
    }
    if len(pieces) == 1:
        return [first]
    first["bulleted_list_item"]["children"] = []
    for more in pieces[1:]:
        first["bulleted_list_item"]["children"].append(paragraph_blocks(more)[0])
    return [first]

def heading_block(level: int, text: str) -> Dict:
    key = "heading_2" if level == 2 else "heading_3"
    return {"object": "block", "type": key, key: {"rich_text": md_inline_to_rich(text)}}

def md_to_blocks(md: str) -> List[Dict]:
    blocks: List[Dict] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("## "):
            blocks.append(heading_block(2, line[3:].strip()))
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(heading_block(3, line[4:].strip()))
            i += 1
            continue
        if lines[i].lstrip().startswith(("- ", "* ")):
            while i < len(lines) and lines[i].lstrip().startswith(("- ", "* ")):
                blocks.extend(bullet_blocks(lines[i].lstrip()[2:].strip()))
                i += 1
            continue
        # paragraph until next blank or structural marker
        para = [line]
        j = i + 1
        while j < len(lines) and lines[j].strip():
            if lines[j].startswith("## ") or lines[j].startswith("### ") or lines[j].lstrip().startswith(("- ", "* ")):
                break
            para.append(lines[j].rstrip())
            j += 1
        blocks.extend(paragraph_blocks("\n".join(para).strip()))
        i = j
    return blocks

# ---------- metadata helpers ----------

def derive_meta_from_filename(path: str):
    base = os.path.splitext(os.path.basename(path))[0]
    podcast = episode = base
    if "__" in base:
        left, right = base.split("__", 1)
        podcast = left.replace("_", " ")
        episode = right.replace("_summary", "").replace("_", " ")
    title = f"{podcast} — {episode}"
    return podcast, episode, title

def load_sidecar(summary_path: str):
    """
    Looks for:
      <summary>_summary.meta.json    or
      <summary_without_suffix>.meta.json
    """
    base = os.path.splitext(summary_path)[0]
    for cand in (base + ".meta.json", base.replace("_summary", "") + ".meta.json"):
        if os.path.exists(cand):
            try:
                return json.load(open(cand, "r", encoding="utf-8"))
            except Exception:
                pass
    return {}

# ---------- duplicate detection ----------

def find_existing_page(client: Client, dbid: str, podcast: str, episode: str):
    """
    Query Notion database to check if a page with the same podcast+episode exists.
    Returns the page ID if found, None otherwise.
    """
    try:
        # Query with filters for exact match
        results = client.databases.query(
            database_id=dbid,
            filter={
                "and": [
                    {
                        "property": "Podcast",
                        "rich_text": {
                            "equals": podcast
                        }
                    },
                    {
                        "property": "Episode",
                        "rich_text": {
                            "equals": episode
                        }
                    }
                ]
            }
        )

        if results.get("results"):
            # Return the first matching page ID
            return results["results"][0]["id"]

        return None
    except Exception as e:
        # If query fails (e.g., property doesn't exist), return None
        print(f"⚠️  Warning: Could not check for duplicates: {e}")
        return None

# ---------- batching ----------

def create_with_batches(client: Client, dbid: str, properties: Dict, blocks: List[Dict]):
    first = blocks[:BATCH_SIZE] if blocks else []
    page = client.pages.create(parent={"database_id": dbid}, properties=properties, children=first)
    pid = page["id"]
    idx = BATCH_SIZE
    while idx < len(blocks):
        client.blocks.children.append(pid, children=blocks[idx:idx+BATCH_SIZE])
        idx += BATCH_SIZE
    return page

def update_with_batches(client: Client, page_id: str, properties: Dict, blocks: List[Dict]):
    """Update existing page properties and replace content"""
    # Update page properties
    client.pages.update(page_id=page_id, properties=properties)

    # Delete existing content blocks (children of the page)
    try:
        existing_blocks = client.blocks.children.list(page_id)
        for block in existing_blocks.get("results", []):
            client.blocks.delete(block["id"])
    except Exception as e:
        print(f"⚠️  Warning: Could not delete old content: {e}")

    # Add new content in batches
    idx = 0
    while idx < len(blocks):
        client.blocks.children.append(page_id, children=blocks[idx:idx+BATCH_SIZE])
        idx += BATCH_SIZE

    return {"id": page_id}

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("summary_path")
    ap.add_argument("--published")  # ISO 8601 date or datetime
    ap.add_argument("--url")
    ap.add_argument("--tags", help="comma-separated")
    args = ap.parse_args()

    token = os.getenv("NOTION_TOKEN")
    dbid = os.getenv("NOTION_DATABASE_ID")
    if not token or not dbid:
        raise RuntimeError("Set NOTION_TOKEN and NOTION_DATABASE_ID")

    content = open(args.summary_path, "r", encoding="utf-8").read()
    podcast, episode, title = derive_meta_from_filename(args.summary_path)

    # merge CLI metadata with sidecar meta if present
    meta = load_sidecar(args.summary_path)
    published = args.published or meta.get("published")
    url = args.url or meta.get("link") or meta.get("url")
    tags = [t.strip() for t in (args.tags.split(",") if args.tags else meta.get("tags", [])) if t.strip()]
    podcast = meta.get("podcast", podcast)
    episode = meta.get("episode", episode)

    client = Client(auth=token)
    blocks = md_to_blocks(content) or paragraph_blocks(content)

    # Check if page already exists
    existing_page_id = find_existing_page(client, dbid, podcast, episode)

    base_props = {
        "Podcast": {"rich_text": [{"text": {"content": podcast}}]},
        "Episode": {"rich_text": [{"text": {"content": episode}}]},
    }
    if published:
        base_props["Published"] = {"date": {"start": published}}
    if url:
        base_props["URL"] = {"url": url}
    if tags:
        base_props["Tags"] = {"multi_select": [{"name": t} for t in tags]}

    # If page exists, update it instead of creating duplicate
    if existing_page_id:
        # try with "Title" then "Name" for the title property
        last_err = None
        for title_prop in ("Title", "Name"):
            try:
                props = {title_prop: {"title": [{"text": {"content": title}}]}, **base_props}
                page = update_with_batches(client, existing_page_id, props, blocks)
                print(f"♻️  Updated existing Notion page with {title_prop}: {page.get('id')}")
                return
            except Exception as e:
                last_err = e
        raise last_err
    else:
        # try with "Title" then "Name" for the title property
        last_err = None
        for title_prop in ("Title", "Name"):
            try:
                props = {title_prop: {"title": [{"text": {"content": title}}]}, **base_props}
                page = create_with_batches(client, dbid, props, blocks)
                print(f"✅ Created Notion page with {title_prop}: {page.get('id')}")
                return
            except Exception as e:
                last_err = e
        raise last_err

if __name__ == "__main__":
    main()