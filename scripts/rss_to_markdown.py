import os
import re
import textwrap
import feedparser
from slugify import slugify
from datetime import datetime

FEEDS = [
    {
        "url": "https://thechenabtimes.com/news/featured/feed",
        "folder": "featured",
        "label": "Featured",
    },
    {
        "url": "https://thechenabtimes.com/news/op-ed/feed",
        "folder": "op-ed",
        "label": "Op-Ed",
    },
]

MAX_ENTRIES = 50

def clean_html(raw: str) -> str:
    return re.sub(r"<[^>]+>", "", raw or "").strip()

def extract_content(entry) -> str:
    if hasattr(entry, "content") and entry.content:
        return clean_html(entry.content[0].get("value", ""))
    if hasattr(entry, "summary"):
        return clean_html(entry.summary)
    return ""

def parse_date(entry) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:3]).strftime("%Y-%m-%d")
    return datetime.today().strftime("%Y-%m-%d")

def build_markdown(entry, category: str) -> str:
    title   = clean_html(entry.get("title", "Untitled"))
    date    = parse_date(entry)
    link    = entry.get("link", "")
    author  = clean_html(entry.get("author", "The Chenab Times"))
    tags    = ", ".join(t["term"] for t in entry.get("tags", []))
    content = extract_content(entry)

    md = textwrap.dedent(f"""\
        ---
        title: "{title}"
        date: {date}
        author: "{author}"
        category: "{category}"
        tags: [{tags}]
        source: "{link}"
        ---

        # {title}

        **By {author} | {date}**

        {content}

        ---
        *Originally published at [{link}]({link})*
    """)
    return md

def save_article(md_content: str, folder: str, slug: str) -> bool:
    year_match = re.search(r"date: (\d{4})", md_content)
    year = year_match.group(1) if year_match else "misc"
    dest_dir = os.path.join(folder, year)
    os.makedirs(dest_dir, exist_ok=True)
    filepath = os.path.join(dest_dir, f"{slug}.md")
    if os.path.exists(filepath):
        return False
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    return True

def main():
    total_new = 0
    for feed_cfg in FEEDS:
        url    = feed_cfg["url"]
        folder = feed_cfg["folder"]
        label  = feed_cfg["label"]
        print(f"\n Fetching {label} feed: {url}")
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            print(f"    Could not parse feed.")
            continue
        entries = feed.entries[:MAX_ENTRIES] if MAX_ENTRIES else feed.entries
        print(f"    Found {len(entries)} entries.")
        new_count = 0
        for entry in entries:
            title = clean_html(entry.get("title", "untitled"))
            slug  = slugify(title)[:80]
            date  = parse_date(entry)
            slug  = f"{date}-{slug}"
            md = build_markdown(entry, label)
            written = save_article(md, folder, slug)
            if written:
                print(f"    Saved: {slug}.md")
                new_count += 1
            else:
                print(f"    Skipped: {slug}.md")
        print(f"    {new_count} new article(s) added for {label}.")
        total_new += new_count
    print(f"\n Sync complete. {total_new} new article(s) total.")

if __name__ == "__main__":
    main()
