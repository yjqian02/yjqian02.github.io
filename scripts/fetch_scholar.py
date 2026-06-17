"""
Fetch publications from Semantic Scholar and write to publications.bib.

Strategy: rather than searching by author name (which can match the wrong
person), we search for a known distinctive paper title to resolve the exact
Semantic Scholar author ID for *this* Alice Qian, then pull all papers
attributed to that specific ID.

Uses only Python stdlib — no extra pip dependencies.

Usage:
    python scripts/fetch_scholar.py
"""

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Distinctive paper titles used to resolve Alice's S2 author ID.
# We search for each in order and stop at the first hit where an author
# named "Qian" appears.  Titles don't need to be exact — S2 is fuzzy.
ANCHOR_PAPERS = [
    "AURA Amplifying Understanding Resilience Awareness Responsible AI Content Work",
    "Worker Discretion Crowdsourced Responsible AI Content Work",
    "Human Factor AI Red Teaming Perspectives Social Collaborative Computing",
    "Personalizing content moderation social media user perspectives",
]

AUTHOR_LAST_NAME = "qian"   # used to pick the right author from a paper's author list
PAPER_FIELDS = (
    "title,authors,year,venue,abstract,externalIds,publicationTypes,journal"
)
S2_BASE = "https://api.semanticscholar.org/graph/v1"
OUTPUT_FILE = Path(__file__).parent.parent / "publications.bib"

# ──────────────────────────────────────────────────────────────────────────────


def s2_get(path: str, params: dict | None = None) -> dict:
    url = S2_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "publications-sync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"S2 API {exc.code} for {url}") from exc


def resolve_author_id() -> str:
    """
    Search for each anchor paper in turn; return the S2 author ID of the
    author whose last name matches AUTHOR_LAST_NAME.
    """
    for query in ANCHOR_PAPERS:
        print(f"  Trying anchor: '{query[:60]}…'")
        try:
            data = s2_get("/paper/search", {
                "query": query,
                "fields": "title,authors",
                "limit": 5,
            })
        except RuntimeError as exc:
            print(f"    Warning: {exc}")
            continue

        for paper in data.get("data", []):
            for author in paper.get("authors", []):
                name = author.get("name", "")
                if AUTHOR_LAST_NAME in name.lower():
                    author_id = author["authorId"]
                    print(f"  Found: '{name}' → S2 author ID {author_id}")
                    print(f"  (matched via paper: '{paper['title'][:70]}')")
                    return author_id

        time.sleep(0.5)

    raise RuntimeError(
        "Could not resolve S2 author ID from any anchor paper. "
        "Check that the papers are indexed on Semantic Scholar."
    )


def get_all_papers(author_id: str) -> list[dict]:
    all_papers: list[dict] = []
    offset = 0
    limit = 100
    while True:
        data = s2_get(f"/author/{author_id}/papers", {
            "fields": PAPER_FIELDS,
            "limit": limit,
            "offset": offset,
        })
        batch = data.get("data", [])
        all_papers.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.3)
    return all_papers


def make_key(authors: list[dict], year: str, title: str) -> str:
    last = "unknown"
    if authors:
        full = authors[0].get("name", "")
        last = re.sub(r"[^a-z]", "", full.split()[-1].lower())
    words = re.findall(r"[a-zA-Z]+", title)
    first = words[0].lower() if words else "untitled"
    return f"{last}{year}{first}"


def paper_to_bibtex(paper: dict) -> str:
    title = paper.get("title") or "Unknown Title"
    year = str(paper.get("year") or "0000")
    authors = paper.get("authors") or []
    author_str = " and ".join(a.get("name", "") for a in authors)

    journal_info = paper.get("journal") or {}
    venue = journal_info.get("name") or paper.get("venue") or ""
    volume = journal_info.get("volume", "")
    pages = journal_info.get("pages", "")

    abstract = (paper.get("abstract") or "").replace("{", "").replace("}", "")
    if len(abstract) > 600:
        abstract = abstract[:600] + "..."

    ext_ids = paper.get("externalIds") or {}
    doi = ext_ids.get("DOI", "")
    arxiv_id = ext_ids.get("ArXiv", "")

    pub_types = [t.lower() for t in (paper.get("publicationTypes") or [])]
    venue_lower = venue.lower()

    if "journalarticle" in pub_types:
        entry_type = "article"
    elif "conference" in pub_types or any(
        kw in venue_lower for kw in ["conference", "proceedings", "workshop", "cscw", "chi", "acm"]
    ):
        entry_type = "inproceedings"
    else:
        entry_type = "article"

    key = make_key(authors, year, title)
    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title     = {{{title}}},")
    lines.append(f"  author    = {{{author_str}}},")
    lines.append(f"  year      = {{{year}}},")
    if venue:
        field = "journal" if entry_type == "article" else "booktitle"
        lines.append(f"  {field:<9} = {{{venue}}},")
    if volume:
        lines.append(f"  volume    = {{{volume}}},")
    if pages:
        lines.append(f"  pages     = {{{pages}}},")
    if abstract:
        lines.append(f"  abstract  = {{{abstract}}},")
    if doi:
        lines.append(f"  doi       = {{{doi}}},")
    if arxiv_id and not doi:
        lines.append(f"  url       = {{https://arxiv.org/abs/{arxiv_id}}},")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    print("Resolving Semantic Scholar author ID from known papers...")
    try:
        author_id = resolve_author_id()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nFetching all papers for author ID {author_id}...")
    try:
        papers = get_all_papers(author_id)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not papers:
        print("No papers returned. publications.bib not updated.")
        sys.exit(1)

    papers.sort(key=lambda p: p.get("year") or 0, reverse=True)
    entries = [paper_to_bibtex(p) for p in papers]

    content = "\n\n".join(entries) + "\n"
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"\nWrote {len(entries)} entries to {OUTPUT_FILE}")
    for p in papers:
        print(f"  {p.get('year', '?')}  {(p.get('title') or '')[:70]}")


if __name__ == "__main__":
    main()
