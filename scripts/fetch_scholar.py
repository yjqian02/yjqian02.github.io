"""
Fetch publications from Semantic Scholar and write to publications.bib.

Uses the Semantic Scholar public API (no key required, stdlib only).
Run locally or via the sync-google-scholar GitHub Actions workflow.

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
AUTHOR_NAME = "Alice Qian"
# Keywords used to disambiguate if multiple authors share the name.
# Checked against affiliation strings (case-insensitive).
AFFILIATION_HINTS = ["carnegie mellon", "cmu", "hcii", "university of minnesota"]

S2_BASE = "https://api.semanticscholar.org/graph/v1"
OUTPUT_FILE = Path(__file__).parent.parent / "publications.bib"
PAPER_FIELDS = "title,authors,year,venue,abstract,externalIds,publicationTypes,journal"
# ──────────────────────────────────────────────────────────────────────────────


def s2_get(path: str, params: dict | None = None) -> dict:
    url = S2_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"S2 API error {exc.code} for {url}") from exc


def find_author_id() -> str:
    data = s2_get("/author/search", {
        "query": AUTHOR_NAME,
        "fields": "authorId,name,affiliations,paperCount",
        "limit": 10,
    })
    candidates = data.get("data", [])
    if not candidates:
        raise RuntimeError(f"No Semantic Scholar authors found for '{AUTHOR_NAME}'")

    # Prefer an author whose affiliation matches a known institution
    for author in candidates:
        affils = " ".join(
            a.get("name", "").lower() for a in author.get("affiliations", [])
        )
        if any(hint in affils for hint in AFFILIATION_HINTS):
            print(f"Matched author: {author['name']} (id={author['authorId']}, "
                  f"papers={author.get('paperCount', '?')})")
            return author["authorId"]

    # Fall back to highest paper count if no affiliation hint matched
    best = max(candidates, key=lambda a: a.get("paperCount", 0))
    print(f"No affiliation match; using highest-papercount result: "
          f"{best['name']} (id={best['authorId']})")
    return best["authorId"]


def get_papers(author_id: str) -> list[dict]:
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
        time.sleep(0.5)
    return all_papers


def make_key(authors: list[dict], year: str, title: str) -> str:
    """Generate a stable BibTeX key: firstauthorlastname + year + firsttitleword."""
    if authors:
        full_name = authors[0].get("name", "unknown")
        last = full_name.split()[-1].lower()
        last = re.sub(r"[^a-z]", "", last)
    else:
        last = "unknown"
    title_words = re.findall(r"[a-zA-Z]+", title)
    first_word = title_words[0].lower() if title_words else "untitled"
    return f"{last}{year}{first_word}"


def paper_to_bibtex(paper: dict) -> str:
    title = paper.get("title") or "Unknown Title"
    year = str(paper.get("year") or "0000")
    authors = paper.get("authors") or []
    author_str = " and ".join(a.get("name", "") for a in authors)

    journal_info = paper.get("journal") or {}
    journal_name = journal_info.get("name", "") or paper.get("venue", "") or ""
    volume = journal_info.get("volume", "")
    pages = journal_info.get("pages", "")

    abstract = (paper.get("abstract") or "").replace("{", "").replace("}", "")
    if len(abstract) > 600:
        abstract = abstract[:600] + "..."

    doi = (paper.get("externalIds") or {}).get("DOI", "")
    arxiv_id = (paper.get("externalIds") or {}).get("ArXiv", "")

    pub_types = [t.lower() for t in (paper.get("publicationTypes") or [])]
    venue_lower = journal_name.lower()

    if "journalarticle" in pub_types:
        entry_type = "article"
    elif "conference" in pub_types or any(
        kw in venue_lower for kw in ["conference", "proceedings", "workshop", "cscw", "chi"]
    ):
        entry_type = "inproceedings"
    else:
        entry_type = "article"  # default for preprints / misc

    key = make_key(authors, year, title)
    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title     = {{{title}}},")
    lines.append(f"  author    = {{{author_str}}},")
    lines.append(f"  year      = {{{year}}},")

    if journal_name:
        field = "journal" if entry_type == "article" else "booktitle"
        lines.append(f"  {field:<9} = {{{journal_name}}},")
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
    print(f"Looking up '{AUTHOR_NAME}' on Semantic Scholar...")
    try:
        author_id = find_author_id()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching papers for author id={author_id}...")
    try:
        papers = get_papers(author_id)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not papers:
        print("No papers found. publications.bib not updated.")
        sys.exit(1)

    # Sort newest first
    papers.sort(key=lambda p: p.get("year") or 0, reverse=True)

    entries = [paper_to_bibtex(p) for p in papers]
    content = "\n\n".join(entries) + "\n"
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
