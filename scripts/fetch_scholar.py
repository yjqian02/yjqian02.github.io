"""
Fetch publications from a Google Scholar profile and write both
publications.bib and Hugo Blox content folders to content/publication/.

The script is self-contained (stdlib only) and works identically when
run locally or in GitHub Actions.  Folders that contain a .keep file
are left untouched (manually managed entries).

Usage:
    python scripts/fetch_scholar.py
"""

import re
import sys
import time
import json
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
SCHOLAR_USER_ID  = "9EeaJAkAAAAJ"
REPO_ROOT        = Path(__file__).parent.parent
OUTPUT_BIB       = REPO_ROOT / "publications.bib"
OUTPUT_PUB_DIR   = REPO_ROOT / "content" / "publication"
PAGE_SIZE        = 100
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


# ── HTML parsers ──────────────────────────────────────────────────────────────

class ScholarProfileParser(HTMLParser):
    """Extract publication rows from a Scholar profile page."""

    def __init__(self):
        super().__init__()
        self.papers: list[dict] = []
        self._in_row = False
        self._cur: dict | None = None
        self._gray_count = 0
        self._capture: str | None = None
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()

        if tag == "tr" and "gsc_a_tr" in classes:
            self._in_row = True
            self._cur = {"title": "", "authors": "", "venue": "", "year": "", "citation_url": ""}
            self._gray_count = 0
            return

        if not self._in_row or self._cur is None:
            return

        if tag == "a" and "gsc_a_at" in classes and self._capture is None:
            self._capture = "title"
            self._depth = 1
            # Capture the href so we can later fetch the detail page
            href = attrs.get("href", "")
            if href and self._cur is not None:
                self._cur["citation_url"] = href
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
            self._cur[self._capture] += data


class ScholarCitationParser(HTMLParser):
    """Extract the primary external URL from a Scholar citation detail page."""

    def __init__(self):
        super().__init__()
        self.external_url: str = ""
        self._found = False

    def handle_starttag(self, tag, attrs):
        if self._found:
            return
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "").split()
        # The main paper link on a citation detail page uses this class
        if tag == "a" and "gsc_oci_title_link" in classes:
            href = attrs_dict.get("href", "")
            # Skip relative Scholar-internal links
            if href and not href.startswith("/citations") and not href.startswith("/scholar"):
                self.external_url = href
                self._found = True


# ── Fetch ─────────────────────────────────────────────────────────────────────

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
        time.sleep(2)

    return papers


def fetch_paper_url(citation_url: str) -> str:
    """Fetch a Scholar citation detail page and return the primary external URL."""
    full_url = "https://scholar.google.com" + citation_url
    try:
        req = urllib.request.Request(full_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        parser = ScholarCitationParser()
        parser.feed(html)
        url = parser.external_url
        # Convert arXiv abstract page to direct PDF
        if url and "arxiv.org/abs/" in url:
            url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
        return url
    except Exception as exc:
        print(f"    Warning: could not fetch detail page: {exc}", file=sys.stderr)
        return ""


def enrich_with_urls(papers: list[dict]) -> None:
    """Fetch each paper's Scholar detail page to get the external URL."""
    print(f"\nFetching detail pages for {len(papers)} papers...")
    for paper in papers:
        citation_url = paper.get("citation_url", "")
        if not citation_url:
            continue
        title_preview = paper["title"][:55]
        print(f"  [{title_preview}]")
        url = fetch_paper_url(citation_url)
        if url:
            paper["url_pdf"] = url
            print(f"    → {url}")
        else:
            print(f"    → (no link found)")
        time.sleep(1.5)


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_venue_year(venue_raw: str) -> tuple[str, str]:
    m = re.search(r"\b(19|20)\d{2}\b", venue_raw)
    year = m.group(0) if m else ""
    venue = venue_raw[:m.start()].strip().rstrip(",") if m else venue_raw.strip()
    return venue, year


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def make_folder_name(authors: str, year: str, title: str) -> str:
    """e.g. qian-2025-aura"""
    last = "unknown"
    if authors:
        first_author = authors.split(",")[0].strip()
        last = re.sub(r"[^a-z]", "", first_author.split()[-1].lower())
    words = re.findall(r"[a-zA-Z]+", title)
    first_word = words[0].lower() if words else "untitled"
    return f"{last}-{year}-{first_word}"


def make_bib_key(authors: str, year: str, title: str) -> str:
    """e.g. qian2025aura"""
    last = "unknown"
    if authors:
        first_author = authors.split(",")[0].strip()
        last = re.sub(r"[^a-z]", "", first_author.split()[-1].lower())
    words = re.findall(r"[a-zA-Z]+", title)
    first_word = words[0].lower() if words else "untitled"
    return f"{last}{year}{first_word}"


def authors_to_list(authors_raw: str) -> list[str]:
    """'Alice Qian, Bob Smith, ...' → ['Alice Qian', 'Bob Smith', ...]"""
    cleaned = authors_raw.replace("…", "").rstrip(",").strip()
    return [a.strip() for a in cleaned.split(",") if a.strip()]


def venue_to_entry_type(venue: str) -> str:
    v = venue.lower()
    if any(kw in v for kw in ["proceedings", "conference", "workshop", "symposium", "cscw", "chi"]):
        return "inproceedings"
    return "article"


# Ordered list of (keywords, short_tag). First match wins.
VENUE_SHORT_MAP: list[tuple[list[str], str]] = [
    # HCI / CHI family
    (["chi conference", "human factors in computing systems", "proceedings of chi", "acm chi"], "CHI"),
    (["cscw", "computer-supported cooperative work", "proceedings of the acm on human-computer interaction", "pacmhci"], "CSCW"),
    (["uist", "user interface software and technology"], "UIST"),
    (["assets", "assistive technology"], "ASSETS"),
    (["iui", "intelligent user interfaces"], "IUI"),
    (["dis ", "designing interactive systems"], "DIS"),
    (["group conference", " group '", "acm group"], "GROUP"),
    (["ecscw"], "ECSCW"),
    (["interact "], "INTERACT"),
    (["nordichi"], "NordiCHI"),
    # AI Ethics / Safety
    (["facct", "fairness, accountability", "fat*", "fatml"], "FAccT"),
    (["aies", "ai, ethics, and society"], "AIES"),
    (["eaamo", "equity and access in algorithms"], "EAAMO"),
    # NLP / ML
    (["emnlp"], "EMNLP"),
    (["naacl"], "NAACL"),
    (["neurips", "neural information processing systems"], "NeurIPS"),
    (["iclr", "international conference on learning representations"], "ICLR"),
    (["icml", "international conference on machine learning"], "ICML"),
    # Social / Web Computing
    (["icwsm"], "ICWSM"),
    (["websci", "web science"], "WebSci"),
    (["world wide web", " www "], "WWW"),
    (["wsdm"], "WSDM"),
    (["kdd"], "KDD"),
    (["recsys"], "RecSys"),
    # Security / Privacy
    (["soups", "symposium on usable privacy"], "SOUPS"),
    (["ieee symposium on security", "ieee s&p"], "IEEE S&P"),
    (["acm ccs", " ccs "], "CCS"),
    (["usenix security"], "USENIX Security"),
    # Journals
    (["tochi", "transactions on computer-human interaction"], "TOCHI"),
    (["tacl", "transactions of the association for computational linguistics"], "TACL"),
    (["communications of the acm", "cacm"], "CACM"),
    (["big data & society"], "Big Data & Society"),
    # Preprint
    (["arxiv"], "arXiv"),
]


def detect_venue_short(venue: str) -> str:
    """Return a short venue tag (e.g. 'CHI', 'CSCW') from a full venue string."""
    if not venue:
        return ""
    v = venue.lower()
    for keywords, short in VENUE_SHORT_MAP:
        if any(kw in v for kw in keywords):
            return short
    return ""


# ── BibTeX ────────────────────────────────────────────────────────────────────

def paper_to_bibtex(paper: dict) -> str:
    title = paper["title"].strip()
    authors_raw = paper.get("authors", "").strip()
    venue_raw = paper.get("venue", "").strip()
    year_field = paper.get("year", "").strip()

    venue, inferred_year = parse_venue_year(venue_raw)
    year = year_field or inferred_year or "0000"

    author_parts = authors_to_list(authors_raw)
    author_str = " and ".join(author_parts)

    entry_type = venue_to_entry_type(venue)
    key = make_bib_key(authors_raw, year, title)
    venue_field = "booktitle" if entry_type == "inproceedings" else "journal"

    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title  = {{{title}}},")
    lines.append(f"  author = {{{author_str}}},")
    lines.append(f"  year   = {{{year}}},")
    if venue:
        lines.append(f"  {venue_field} = {{{venue}}},")
    lines.append("}")
    return "\n".join(lines)


# ── Hugo markdown ─────────────────────────────────────────────────────────────

def paper_to_hugo_markdown(paper: dict) -> tuple[str, str]:
    """Returns (folder_name, markdown_content)."""
    import json

    title = paper["title"].strip()
    authors_raw = paper.get("authors", "").strip()
    venue_raw = paper.get("venue", "").strip()
    year_field = paper.get("year", "").strip()

    venue, inferred_year = parse_venue_year(venue_raw)
    year = year_field or inferred_year or "0000"
    date = f"{year}-01-01"

    author_list = authors_to_list(authors_raw)
    entry_type = venue_to_entry_type(venue)
    pub_type = "paper-conference" if entry_type == "inproceedings" else "article-journal"

    venue_short = detect_venue_short(venue) or detect_venue_short(venue_raw)

    folder = make_folder_name(authors_raw, year, title)

    safe_title = title.replace("'", "''")
    safe_venue = venue.replace("'", "''") if venue else ""
    authors_yaml = "\n".join(f"- {a}" for a in author_list)
    venue_short_line = f"venue_short: '{venue_short}'\n" if venue_short else ""

    url_pdf = paper.get("url_pdf", "")
    url_pdf_line = f"url_pdf: '{url_pdf}'\n" if url_pdf else ""

    content = f"""---
title: '{safe_title}'
authors:
{authors_yaml}
date: '{date}'
publishDate: '{date}'
publication_types:
- {pub_type}
publication: '{"*" + safe_venue + "*" if safe_venue else ""}'
{venue_short_line}{url_pdf_line}featured: false
---
"""
    return folder, content


# ── Write outputs ─────────────────────────────────────────────────────────────

def write_bib(papers: list[dict]) -> None:
    entries = [paper_to_bibtex(p) for p in papers]
    OUTPUT_BIB.write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {OUTPUT_BIB.name}")


def write_hugo_folders(papers: list[dict]) -> None:
    OUTPUT_PUB_DIR.mkdir(parents=True, exist_ok=True)

    # Collect folder names the scraper will manage
    scraped_folders: set[str] = set()

    for paper in papers:
        folder_name, content = paper_to_hugo_markdown(paper)
        scraped_folders.add(folder_name)
        folder_path = OUTPUT_PUB_DIR / folder_name

        # Never overwrite manually managed entries
        if (folder_path / ".keep").exists():
            print(f"  Skipping manually managed: {folder_name}")
            continue

        folder_path.mkdir(exist_ok=True)

        # Preserve manual overrides from existing index.md
        existing_md = folder_path / "index.md"
        if existing_md.exists():
            import re as _re
            existing_text = existing_md.read_text(encoding="utf-8")

            # date_manual: true → keep the existing date field
            if "date_manual: true" in existing_text:
                m = _re.search(r"date: '([^']+)'", existing_text)
                if m:
                    content = _re.sub(r"date: '[^']+'", f"date: '{m.group(1)}'", content, count=1)
                    content = content.replace("featured: false", "date_manual: true\nfeatured: false")
                    print(f"  Kept manual date for: {folder_name}")

            # venue_short_override: 'X' → use X for venue_short, re-add override field
            m2 = _re.search(r"venue_short_override: '([^']*)'", existing_text)
            if m2:
                override = m2.group(1)
                content = _re.sub(r"venue_short: '[^']*'\n", "", content)
                content = content.replace(
                    "featured: false",
                    f"venue_short: '{override}'\nvenue_short_override: '{override}'\nfeatured: false",
                )
                print(f"  Kept venue_short_override for: {folder_name}")

            # url_pdf_manual: true → keep the existing url_pdf and ignore freshly scraped one
            if "url_pdf_manual: true" in existing_text:
                m3 = _re.search(r"url_pdf: '([^']*)'", existing_text)
                existing_url = m3.group(1) if m3 else ""
                content = _re.sub(r"url_pdf: '[^']*'\n", "", content)
                content = content.replace(
                    "featured: false",
                    f"url_pdf: '{existing_url}'\nurl_pdf_manual: true\nfeatured: false",
                )
                print(f"  Kept manual url_pdf for: {folder_name}")

            # If the scraper failed to fetch a URL, fall back to preserving the existing one
            elif "url_pdf: '" not in content and "url_pdf: '" in existing_text:
                m4 = _re.search(r"url_pdf: '([^']+)'", existing_text)
                if m4:
                    content = content.replace(
                        "featured: false",
                        f"url_pdf: '{m4.group(1)}'\nfeatured: false",
                    )
                    print(f"  Preserved existing url_pdf for: {folder_name}")

        (folder_path / "index.md").write_text(content, encoding="utf-8")

    # Remove folders that are no longer in the scraped set,
    # unless they have a .keep file
    for existing in OUTPUT_PUB_DIR.iterdir():
        if not existing.is_dir():
            continue
        if (existing / ".keep").exists():
            continue
        if existing.name not in scraped_folders:
            import shutil
            shutil.rmtree(existing)
            print(f"  Removed stale folder: {existing.name}")

    print(f"Hugo publication folders updated in {OUTPUT_PUB_DIR.relative_to(REPO_ROOT)}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Fetching Google Scholar profile for user: {SCHOLAR_USER_ID}")
    papers = fetch_all_papers()

    if not papers:
        print("No papers found. Check that the profile is public and the user ID is correct.")
        sys.exit(1)

    # Sort newest first
    def sort_key(p):
        _, y = parse_venue_year(p.get("venue", ""))
        return int(p.get("year") or y or 0)

    papers.sort(key=sort_key, reverse=True)

    print(f"\nFound {len(papers)} papers:")
    for p in papers:
        _, y = parse_venue_year(p.get("venue", ""))
        year = p.get("year") or y or "????"
        print(f"  {year}  {p['title'][:70]}")

    enrich_with_urls(papers)

    print()
    write_bib(papers)
    write_hugo_folders(papers)


if __name__ == "__main__":
    main()
