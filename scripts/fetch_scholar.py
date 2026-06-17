"""
Scrape publications directly from a Google Scholar profile page and write
to publications.bib.  Uses only Python stdlib — no pip dependencies.

Usage:
    python scripts/fetch_scholar.py
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
SCHOLAR_USER_ID = "9EeaJAkAAAAJ"
OUTPUT_FILE = Path(__file__).parent.parent / "publications.bib"
PAGE_SIZE = 100   # max papers per request Scholar will return
# ──────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ── HTML parser ───────────────────────────────────────────────────────────────

class ScholarProfileParser(HTMLParser):
    """
    Parses the Scholar profile HTML and extracts publication rows.

    Each row (<tr class="gsc_a_tr">) contains:
      - Title:   <a class="gsc_a_at">
      - Authors: first <div class="gs_gray">
      - Venue:   second <div class="gs_gray">
      - Year:    <span class="gsc_a_h">
    """

    def __init__(self):
        super().__init__()
        self.papers: list[dict] = []
        self._in_row = False
        self._cur: dict | None = None
        self._gray_count = 0          # counts <div class="gs_gray"> inside a row
        self._capture: str | None = None   # which field we're capturing text for
        self._depth = 0               # tag nesting depth inside captured element

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()

        if tag == "tr" and "gsc_a_tr" in classes:
            self._in_row = True
            self._cur = {"title": "", "authors": "", "venue": "", "year": ""}
            self._gray_count = 0
            return

        if not self._in_row or self._cur is None:
            return

        if tag == "a" and "gsc_a_at" in classes and self._capture is None:
            self._capture = "title"
            self._depth = 1
            return

        if tag == "div" and "gs_gray" in classes and self._capture is None:
            self._gray_count += 1
            self._capture = "authors" if self._gray_count == 1 else "venue"
            self._depth = 1
            return

        if tag == "span" and "gsc_a_h" in classes and self._capture is None:
            self._capture = "year"
            self._depth = 1
            return

        # Track nesting depth inside a captured element
        if self._capture is not None:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._capture is not None:
            self._depth -= 1
            if self._depth == 0:
                self._capture = None

        if tag == "tr" and self._in_row:
            if self._cur and self._cur.get("title"):
                self.papers.append(self._cur)
            self._in_row = False
            self._cur = None

    def handle_data(self, data):
        if self._capture and self._cur is not None:
            self._cur[self._capture] = self._cur.get(self._capture, "") + data


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def fetch_page(start: int) -> str:
    url = (
        f"https://scholar.google.com/citations"
        f"?user={SCHOLAR_USER_ID}&sortby=pubdate"
        f"&pagesize={PAGE_SIZE}&cstart={start}&hl=en"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_all_papers() -> list[dict]:
    papers: list[dict] = []
    start = 0
    while True:
        print(f"  Fetching profile page (offset {start})...")
        try:
            html = fetch_page(start)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                print("ERROR: Google rate-limited this request (HTTP 429).", file=sys.stderr)
                print("Try again later or increase the schedule interval.", file=sys.stderr)
            else:
                print(f"ERROR: HTTP {exc.code}", file=sys.stderr)
            sys.exit(1)

        parser = ScholarProfileParser()
        parser.feed(html)
        batch = parser.papers

        if not batch:
            break
        papers.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        time.sleep(2)   # be polite between pages

    return papers


# ── BibTeX conversion ─────────────────────────────────────────────────────────

def parse_venue_year(venue_raw: str) -> tuple[str, str]:
    """Split 'Journal Name, 2024' into (venue, year)."""
    # Year is typically the last 4-digit number
    m = re.search(r"\b(19|20)\d{2}\b", venue_raw)
    year = m.group(0) if m else ""
    venue = venue_raw[:m.start()].strip().rstrip(",") if m else venue_raw.strip()
    return venue, year


def make_key(authors: str, year: str, title: str) -> str:
    last = "unknown"
    if authors:
        first_author = authors.split(",")[0].strip()
        last = re.sub(r"[^a-z]", "", first_author.split()[-1].lower())
    words = re.findall(r"[a-zA-Z]+", title)
    first_word = words[0].lower() if words else "untitled"
    return f"{last}{year}{first_word}"


def paper_to_bibtex(paper: dict) -> str:
    title = paper["title"].strip()
    authors_raw = paper.get("authors", "").strip()
    venue_raw = paper.get("venue", "").strip()
    year_field = paper.get("year", "").strip()

    venue, inferred_year = parse_venue_year(venue_raw)
    year = year_field or inferred_year or "0000"

    # Scholar lists authors as "A Name, B Name, ..." with possible "..." truncation
    authors_clean = authors_raw.replace("…", "et al.").rstrip(",").strip()
    # Convert "First Last, First Last" → "First Last and First Last"
    author_parts = [a.strip() for a in authors_clean.split(",") if a.strip()]
    author_str = " and ".join(author_parts)

    venue_lower = venue.lower()
    if any(kw in venue_lower for kw in
           ["proceedings", "conference", "workshop", "symposium", "cscw", "chi"]):
        entry_type = "inproceedings"
        venue_field = "booktitle"
    elif venue:
        entry_type = "article"
        venue_field = "journal"
    else:
        entry_type = "misc"
        venue_field = None

    key = make_key(authors_raw, year, title)
    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title  = {{{title}}},")
    lines.append(f"  author = {{{author_str}}},")
    lines.append(f"  year   = {{{year}}},")
    if venue_field and venue:
        lines.append(f"  {venue_field} = {{{venue}}},")
    lines.append("}")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Fetching Google Scholar profile for user ID: {SCHOLAR_USER_ID}")
    papers = fetch_all_papers()

    if not papers:
        print("No papers found. Check that the profile is public and the user ID is correct.")
        sys.exit(1)

    entries = [paper_to_bibtex(p) for p in papers]
    content = "\n\n".join(entries) + "\n"
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"\nWrote {len(entries)} entries to {OUTPUT_FILE}:")
    for p in papers:
        _, year = parse_venue_year(p.get("venue", ""))
        year = p.get("year") or year or "????"
        print(f"  {year}  {p['title'][:70]}")


if __name__ == "__main__":
    main()
