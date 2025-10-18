import feedparser
from datetime import datetime, timezone

def get_latest_episode(feed_url: str):
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return None
    e = feed.entries[0]
    mp3 = e.enclosures[0].href if getattr(e, "enclosures", None) else None
    pub = None
    if getattr(e, "published_parsed", None):
        pub = datetime(*e.published_parsed[:6], tzinfo=timezone.utc).isoformat()
    return {
        "title": getattr(e, "title", "Untitled"),
        "link": getattr(e, "link", ""),
        "mp3_url": mp3,
        "published": pub,
        "id": getattr(e, "id", getattr(e, "guid", getattr(e, "link", ""))),
    }

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if not url:
        print("Usage: python3 scripts/fetch_feed.py <RSS_URL>")
        sys.exit(1)
    item = get_latest_episode(url)
    print(item)
