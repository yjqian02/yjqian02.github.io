"""
Fetch publications from Google Scholar and write to publications.bib.

Uses the `scholarly` library to pull papers by author ID and converts them
to BibTeX. Run locally or via the sync-google-scholar GitHub Actions workflow.

Usage:
    pip install scholarly
    python scripts/fetch_scholar.py
"""

import sys
import re
import time
import random
from pathlib import Path

SCHOLAR_ID = "9EeaJAkAAAAJ"
OUTPUT_FILE = Path(__file__).parent.parent / "publications.bib"


def sanitize_key(title: str, year: str | int) -> str:
    """Build a short BibTeX key from title + year."""
    words = re.findall(r"[a-zA-Z]+", title)
    slug = "_".join(w.lower() for w in words[:3])
    return f"{slug}_{year}"


def pub_to_bibtex(pub: dict) -> str:
    """Convert a scholarly publication dict to a BibTeX entry string."""
    bib = pub.get("bib", {})
    title = bib.get("title", "Unknown Title")
    year = bib.get("pub_year", "0000")
    authors = bib.get("author", "Unknown Author")
    venue = bib.get("venue", "")
    abstract = bib.get("abstract", "")
    pub_url = pub.get("pub_url", "")

    # Determine entry type
    entry_type = "article"
    venue_lower = venue.lower()
    for conf_keyword in ["conference", "proceedings", "workshop", "symposium", "cscw", "chi", "acm", "ieee"]:
        if conf_keyword in venue_lower:
            entry_type = "inproceedings"
            break

    key = sanitize_key(title, year)

    lines = [f"@{entry_type}{{{key},"]
    lines.append(f'  title = {{{title}}},')
    lines.append(f'  author = {{{authors}}},')
    lines.append(f'  year = {{{year}}},')
    if venue:
        field = "journal" if entry_type == "article" else "booktitle"
        lines.append(f'  {field} = {{{venue}}},')
    if abstract:
        # Truncate very long abstracts
        short_abstract = abstract[:800] + "..." if len(abstract) > 800 else abstract
        short_abstract = short_abstract.replace("{", "").replace("}", "")
        lines.append(f'  abstract = {{{short_abstract}}},')
    if pub_url:
        lines.append(f'  url = {{{pub_url}}},')
    lines.append("}")
    return "\n".join(lines)


def fetch_publications() -> list[str]:
    try:
        from scholarly import scholarly, ProxyGenerator  # type: ignore
    except ImportError:
        print("ERROR: `scholarly` not installed. Run: pip install scholarly", file=sys.stderr)
        sys.exit(1)

    # Attempt to use free proxies to avoid Google blocking
    try:
        pg = ProxyGenerator()
        if pg.FreeProxies():
            scholarly.use_proxy(pg)
            print("Using free proxy for Scholar requests.")
        else:
            print("No free proxies available; attempting direct connection.")
    except Exception as e:
        print(f"Proxy setup failed ({e}); attempting direct connection.")

    print(f"Fetching author profile for Scholar ID: {SCHOLAR_ID}")
    try:
        author = scholarly.search_author_id(SCHOLAR_ID)
        scholarly.fill(author, sections=["publications"])
    except Exception as e:
        print(f"ERROR: Could not fetch author profile: {e}", file=sys.stderr)
        sys.exit(1)

    entries = []
    pubs = author.get("publications", [])
    print(f"Found {len(pubs)} publications. Fetching details...")

    for i, pub in enumerate(pubs):
        try:
            # Stagger requests to avoid rate limiting
            time.sleep(random.uniform(1.5, 3.5))
            filled = scholarly.fill(pub)
            entries.append(pub_to_bibtex(filled))
            title = filled.get("bib", {}).get("title", "?")
            print(f"  [{i+1}/{len(pubs)}] {title}")
        except Exception as e:
            title = pub.get("bib", {}).get("title", "unknown")
            print(f"  WARN: skipping '{title}': {e}", file=sys.stderr)

    return entries


def main() -> None:
    entries = fetch_publications()
    if not entries:
        print("No publications fetched. publications.bib not updated.")
        sys.exit(1)

    content = "\n\n".join(entries) + "\n"
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"\nWrote {len(entries)} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
