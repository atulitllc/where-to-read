#!/usr/bin/env python3
"""Static pages for Where to Read. No book files. Covers are hotlinked."""
import html
import json
import re
from pathlib import Path

from blurbs import history_copy

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"
BRAND = "Where to Read"
FORBIDDEN = re.compile(r"\b(pdf|epub|mobi|download|free ebook)\b", re.I)

def esc(s):
    return html.escape(s if s is not None else "", quote=True)

def external_attrs(url):
    """Return safe new-tab attributes for off-site HTTP(S) anchors."""
    if re.match(r"^https?://", url or "", re.I):
        return ' target="_blank" rel="noopener noreferrer"'
    return ""

def boot():
    return """<script>
try {
  var t = localStorage.getItem("wtr-theme");
  if (t !== "light" && t !== "dark") {
    t = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.setAttribute("data-theme", t);
} catch (e) {}
</script>"""

def head(title, description, depth, extra=""):
    prefix = "../" * depth
    # non-PD titles stay noindex even later; every page is noindex on github.io
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<link rel="canonical" href="./">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{boot()}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,500;0,600;1,500&family=Literata:ital,opsz,wght@0,7..72,420;0,7..72,620;1,7..72,420&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}css/site.css">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
{extra}
</head>
"""

def brand_svg():
    return """<svg class="brand-mark" width="36" height="34" viewBox="0 0 96 90" aria-hidden="true">
  <g class="bk">
    <rect x="18" y="16" width="6" height="16" rx="0.6"/>
    <rect x="26" y="8" width="5" height="24" rx="0.6"/>
    <rect x="33" y="14" width="8" height="18" rx="0.6"/>
    <rect x="43" y="4" width="6" height="28" rx="0.6"/>
    <rect x="51" y="12" width="7" height="20" rx="0.6"/>
    <rect x="60" y="18" width="5" height="14" rx="0.6"/>
    <rect x="67" y="11" width="8" height="21" rx="0.6"/>
    <rect x="14" y="38" width="68" height="8"/>
    <path d="M10 50h76v16H10z"/>
    <path d="M7 68h82v16H7z"/>
  </g>
  <rect class="pg edge" x="14" y="32" width="68" height="14" rx="2"/>
  <g class="pg">
    <rect x="14" y="53" width="22" height="1.6"/>
    <rect x="60" y="53" width="22" height="1.6"/>
    <rect x="14" y="56.5" width="22" height="1.6" opacity="0.65"/>
    <rect x="60" y="56.5" width="22" height="1.6" opacity="0.65"/>
    <rect x="12" y="71" width="24" height="1.6"/>
    <rect x="60" y="71" width="24" height="1.6"/>
    <rect x="12" y="74.5" width="24" height="1.6" opacity="0.65"/>
    <rect x="60" y="74.5" width="24" height="1.6" opacity="0.65"/>
    <path d="M40 84V66a8 8 0 0 1 16 0v18z"/>
  </g>
  <g class="bk">
    <circle cx="48" cy="68.5" r="2.7"/>
    <rect x="45.1" y="71.6" width="5.8" height="8.2" rx="2.4"/>
  </g>
  <path class="rib" d="M70 36h6.5v22l-3.25-3.4L70 58z"/>
</svg>"""

# Header wordmark is permanently "booksthere" (no .com). Do not change it back to "Where to Read", and do not scale it horizontally.
# Page titles still say Where to Read. The doorway mark stays.
def header(depth):
    prefix = "../" * depth
    return f"""<a class="skip" href="#content">Skip to content</a>
<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="{prefix}">{brand_svg()}<span class="brand-word">books<span class="brand-accent">there</span></span></a>
    <button type="button" class="theme-toggle" aria-pressed="false" aria-label="Switch between day paper and night lamp">
      <span class="lamp-dot" aria-hidden="true"></span>
      <span class="theme-toggle-label">Night lamp</span>
    </button>
  </div>
</header>
"""

def footer(depth):
    return """<footer class="colophon wrap">
  <p>Where to Read is a catalog of public-domain books. You read them on Open Library. This site does not host copyrighted books.</p>
  <p>Records are from <a href="https://openlibrary.org/" target="_blank" rel="noopener noreferrer">Open Library</a>. Cover images, when a record has one, are loaded from covers.openlibrary.org and are not stored here. Project Gutenberg links open that book’s landing page only.</p>
</footer>
<script src="{prefix}js/theme.js"></script>
</body>
</html>
""".replace("{prefix}", "../" * depth)

def cover_html(book, large=False):
    alt = f"Cover of {book['title']} from Open Library"
    if book.get("cover_i"):
        src = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
    elif book.get("ol_id"):
        src = f"https://covers.openlibrary.org/w/olid/{book['ol_id']}-L.jpg"
    else:
        src = None
    fallback = f'<div class="cover-fallback" role="img" aria-label="{esc(alt)}">{esc(book["title"])}</div>'
    if not src:
        return fallback
    # If Open Library has no image, the request fails and the title panel shows instead.
    return (
        f'<img class="cover" src="{esc(src)}" alt="{esc(alt)}" width="330" height="500" loading="lazy" '
        f'onerror="this.onerror=null;this.hidden=true;if(this.nextElementSibling)this.nextElementSibling.hidden=false;">'
        f'<div class="cover-fallback" hidden>{esc(book["title"])}</div>'
    )

def subject_links(book, subjects, depth):
    prefix = "../" * depth
    parts = []
    for slug in book["subjects"]:
        name = subjects[slug]["name"]
        parts.append(f'<a href="{prefix}subjects/{slug}/">{esc(name)}</a>')
    return " · ".join(parts)

def write(path: Path, text: str):
    if FORBIDDEN.search(text):
        bad = FORBIDDEN.findall(text)
        raise SystemExit(f"forbidden copy in {path}: {bad}")
    if "atulit" in text.lower():
        raise SystemExit(f"Atulit string in {path}")
    if re.search(r"gutenberg\.org/.+\.(epub|mobi|txt)|gutenberg\.org/files/|gutenberg\.org/cache/", text, re.I):
        raise SystemExit(f"gutenberg file link in {path}")
    if "www.gutenberg.org" in text and not re.search(r"https://www\.gutenberg\.org/ebooks/\d+", text):
        # footer doesn't include gutenberg host. book pages must.
        pass
    if "schema.org/Product" in text or "schema.org/Offer" in text or '"@type": "Product"' in text or '"@type": "Offer"' in text:
        raise SystemExit("product schema")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)

def pick_related(book, pool, limit=6):
    pool = [b for b in pool if b["slug"] != book["slug"]]
    if not pool:
        return []
    if len(pool) <= limit:
        return pool
    start = sum(ord(c) for c in book["slug"]) % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(limit)]

def related_list(items, authors, depth):
    prefix = "../" * depth
    lis = []
    for b in items:
        author = authors[b["author"]]
        year = f" <span class=\"meta\">({b['year']})</span>" if b.get("year") else ""
        lis.append(
            '<li><a href="%sbooks/%s/">%s</a>%s <span class="by">· <a href="%sauthors/%s/">%s</a></span></li>' % (
                prefix, b["slug"], esc(b["title"]), year, prefix, author["slug"], esc(author["name"])
            )
        )
    return '<ul class="related">' + "".join(lis) + "</ul>"

def page_book(book, authors, subjects, by_author, by_subject):
    author = authors[book["author"]]
    depth = 2
    prefix = "../../"
    title = f"{book['title']} by {author['name']} | {BRAND}"
    desc = f"A catalog entry for the public-domain book {book['title']} by {author['name']}. Read it on Open Library. This site does not host copyrighted books."
    year = f"{book['year']} · " if book.get("year") else ""
    read_li = ""
    if book.get("read_url"):
        read_li = f'<li><a href="{esc(book["read_url"])}"{external_attrs(book["read_url"])}>Read or borrow on Open Library</a></li>'
    # sameAs is the Open Library work and the Gutenberg landing page only.
    # Borrow links stay in the visible list, never in sameAs.
    same = [book["ol_url"]]
    if book.get("gutenberg_url"):
        same.append(book["gutenberg_url"])
    for link in same:
        if "/borrow/" in link:
            raise SystemExit(f"borrow link in sameAs for {book['slug']}")
    schema = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": book["title"],
        "author": {
            "@type": "Person",
            "name": author["name"],
            "url": f"{prefix}authors/{author['slug']}/",
        },
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "Open Library",
            "value": book["ol_id"],
        },
        "sameAs": same,
        "url": "./",
    }
    if schema["url"] == book["ol_url"] or schema["url"].startswith(("http://", "https://")):
        raise SystemExit(f"Book.url must stay a relative catalog URL for {book['slug']}")
    if book.get("year"):
        schema["datePublished"] = str(book["year"])
    if book.get("cover_i"):
        schema["image"] = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
    extra = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
    same_author = pick_related(book, by_author.get(book["author"], []))
    primary = book["subjects"][0]
    same_subject = pick_related(book, [b for b in by_subject.get(primary, []) if b["author"] != book["author"]])
    related_parts = []
    if same_author:
        related_parts.append(
            f'<h2 class="shelf-label">More by {esc(author["name"])}</h2>'
            + related_list(same_author, authors, depth)
        )
    if same_subject:
        related_parts.append(
            f'<h2 class="shelf-label">More {esc(subjects[primary]["name"].lower())}</h2>'
            + related_list(same_subject, authors, depth)
        )
    related_html = "\n".join(related_parts)
    body = f"""{head(title, desc, depth, extra)}
<body>
{header(depth)}
<main id="content" class="wrap detail-wrap">
  <nav class="crumbs" aria-label="Breadcrumb">
    <a href="{prefix}">Where to Read</a>
    <span aria-hidden="true">/</span>
    <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a>
    <span aria-hidden="true">/</span>
    <span>{esc(book['title'])}</span>
  </nav>
  <article class="book">
    <div class="book-top">
      <div class="book-cover">{cover_html(book)}</div>
      <div class="book-summary">
        <p class="kicker">Public-domain book</p>
        <h1>{esc(book['title'])}</h1>
        <p class="by">by <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a></p>
        <p class="meta">{year}{subject_links(book, subjects, depth)}</p>
        <p class="ol-id">Open Library {esc(book['ol_id'])}</p>
        <p class="blurb">{esc(book['blurb'])}</p>
      </div>
    </div>
    <div class="book-details">
      <p class="history">{esc(history_copy(book, author, subjects))}</p>
      <h2 class="shelf-label">About the author</h2>
      <p class="author-snippet">{esc(author['intro'])} <a href="{prefix}authors/{author['slug']}/">More of this shelf for {esc(author['name'])}</a>.</p>
      <h2 class="shelf-label">Where to read it</h2>
      <ul class="where">
        <li><a href="{esc(book['ol_url'])}"{external_attrs(book['ol_url'])}>Open Library work</a></li>
        {read_li}
        <li><a href="{esc(book['gutenberg_url'])}"{external_attrs(book['gutenberg_url'])}>Project Gutenberg page</a></li>
      </ul>
      <p class="note">Open Library hosts the reading view. Some editions open in the browser; others ask you to borrow. Project Gutenberg links in this catalog open the book’s page, not a file kept here.</p>
      {related_html}
    </div>
  </article>
</main>
{footer(depth)}
"""
    write(ROOT / "books" / book["slug"] / "index.html", body)

def page_author(author, books, subjects):
    depth = 2
    prefix = "../../"
    title = f"{author['name']} | {BRAND}"
    desc = f"Public-domain books by {author['name']} in this catalog. Read them on Open Library. This site does not host copyrighted books."
    items = []
    for b in books:
        items.append(f"""<article class="card">
          <a href="{prefix}books/{b['slug']}/">{cover_html(b)}</a>
          <div>
            <h2><a href="{prefix}books/{b['slug']}/">{esc(b['title'])}</a></h2>
            <p class="meta">{(str(b['year']) + ' · ') if b.get('year') else ''}{subject_links(b, subjects, depth)}</p>
            <p class="blurb">{esc(b['blurb'])}</p>
          </div>
        </article>""")
    body = f"""{head(title, desc, depth)}
<body>
{header(depth)}
<main id="content" class="wrap detail-wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">Where to Read</a> <span aria-hidden="true">/</span> <span>{esc(author['name'])}</span></nav>
  <p class="kicker">Author</p>
  <h1>{esc(author['name'])}</h1>
  <p class="lede">{esc(author['intro'])}</p>
  <hr class="rule">
  <div class="catalog">{''.join(items)}</div>
</main>
{footer(depth)}
"""
    write(ROOT / "authors" / author["slug"] / "index.html", body)

def page_subject(subject, books, authors):
    depth = 2
    prefix = "../../"
    title = f"{subject['name']} books | {BRAND}"
    desc = f"Public-domain {subject['name'].lower()} books in this catalog. Read them on Open Library. This site does not host copyrighted books."
    items = []
    for b in books:
        author = authors[b["author"]]
        items.append(f"""<article class="card">
          <a href="{prefix}books/{b['slug']}/">{cover_html(b)}</a>
          <div>
            <h2><a href="{prefix}books/{b['slug']}/">{esc(b['title'])}</a></h2>
            <p class="by">by <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a></p>
            <p class="blurb">{esc(b['blurb'])}</p>
          </div>
        </article>""")
    body = f"""{head(title, desc, depth)}
<body>
{header(depth)}
<main id="content" class="wrap detail-wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">Where to Read</a> <span aria-hidden="true">/</span> <span>{esc(subject['name'])}</span></nav>
  <p class="kicker">Subject</p>
  <h1>{esc(subject['name'])}</h1>
  <p class="lede">{esc(subject['intro'])}</p>
  <hr class="rule">
  <div class="catalog">{''.join(items)}</div>
</main>
{footer(depth)}
"""
    write(ROOT / "subjects" / subject["slug"] / "index.html", body)

def book_card(b, authors, subjects):
    author = authors[b["author"]]
    year = f"{b['year']} · " if b.get("year") else ""
    return f"""<article class="card">
        <a href="books/{b['slug']}/">{cover_html(b)}</a>
        <div>
          <h2><a href="books/{b['slug']}/">{esc(b['title'])}</a></h2>
          <p class="by">by <a href="authors/{author['slug']}/">{esc(author['name'])}</a></p>
          <p class="meta">{year}{subject_links(b, subjects, 0)}</p>
          <p class="blurb">{esc(b['blurb'])}</p>
        </div>
      </article>"""


TOP_READ = [
    "pride-and-prejudice", "jane-eyre", "frankenstein", "dracula",
    "the-adventures-of-sherlock-holmes", "moby-dick", "adventures-of-huckleberry-finn",
    "great-expectations", "crime-and-punishment", "the-odyssey", "the-great-gatsby",
    "narrative-of-the-life-of-frederick-douglass", "alices-adventures-in-wonderland",
    "the-wonderful-wizard-of-oz", "leaves-of-grass", "the-raven", "walden", "meditations",
]
READ_SHELVES = [
    ("Fiction", "novel", [
        "wuthering-heights", "the-picture-of-dorian-gray", "a-tale-of-two-cities", "little-women",
        "anna-karenina", "the-count-of-monte-cristo", "les-miserables", "don-quixote",
        "the-scarlet-letter", "the-war-of-the-worlds",
    ]),
    ("Kids", "childrens-books", [
        "peter-and-wendy", "the-secret-garden", "anne-of-green-gables", "the-adventures-of-tom-sawyer-complete",
        "at-the-back-of-the-north-wind", "black-beauty", "the-railway-children", "five-children-and-it",
        "little-lord-fauntleroy", "the-water-babies",
    ]),
    ("History", "history", [
        "the-french-revolution-a-history", "an-account-of-egypt", "lays-of-ancient-rome", "caesar-a-sketch",
        "the-history-of-london", "history-of-the-commune-of-1871", "a-brief-history-of-the-united-states",
        "history-of-the-moors-of-spain", "the-life-of-flavius-josephus", "a-general-history-of-the-pyrates",
    ]),
    ("Poetry", "poetry", [
        "paradise-lost", "the-rime-of-the-ancient-mariner", "sonnets-from-the-portuguese",
        "the-complete-works-of-william-shakespeare", "endymion-a-poetic-romance",
        "lyrical-ballads-with-a-few-other-poems-1798", "poems-on-various-subjects-religious-and-moral",
        "the-pied-piper-of-hamelin", "poems-by-william-cullen-bryant", "1914-and-other-poems",
    ]),
]


def pick_books(books, seeds, limit, subject=None, skip=()):
    found = {b["slug"]: b for b in books}
    chosen = []
    seen = set(skip)
    for slug in seeds:
        b = found.get(slug)
        if not b or slug in seen:
            continue
        if subject and subject not in b["subjects"]:
            continue
        chosen.append(b)
        seen.add(slug)
        if len(chosen) == limit:
            return chosen
    pool = [b for b in books if b["slug"] not in seen and (not subject or subject in b["subjects"])]
    pool.sort(key=lambda b: (0 if b.get("featured") else 1, 0 if b.get("cover_i") else 1, len(b["title"]), b["title"].lower()))
    for b in pool:
        chosen.append(b)
        if len(chosen) == limit:
            break
    return chosen


def page_home(catalog, authors, subjects):
    books = catalog["books"]
    depth = 0
    title = f"Public-domain books | {BRAND}"
    desc = "A catalog of public-domain books you can read on Open Library. This site does not host copyrighted books."
    subject_bits = "".join(
        f'<li><a href="subjects/{esc(s["slug"])}/">{esc(s["name"])}</a></li>' for s in catalog["subjects"]
    )
    top = pick_books(books, TOP_READ, 18)
    shelves = [(label, slug, pick_books(books, seeds, 10, subject=slug)) for label, slug, seeds in READ_SHELVES]
    shown = len(top) + sum(len(rows) for _l, _s, rows in shelves)
    if shown > 80:
        raise SystemExit(f"home card cap {shown}")
    shelf_html = [f"""<section class="shelf" aria-labelledby="top-read">
    <div class="shelf-head"><h2 id="top-read" class="shelf-label">Top Read</h2></div>
    <div class="home-rail">{''.join(book_card(b, authors, subjects) for b in top)}</div>
  </section>"""]
    for label, slug, rows in shelves:
        shelf_html.append(f"""<section class="shelf" aria-labelledby="shelf-{esc(slug)}">
    <div class="shelf-head"><h2 id="shelf-{esc(slug)}" class="shelf-label">{esc(label)}</h2><a class="see-all" href="subjects/{esc(slug)}/">See all</a></div>
    <div class="home-rail">{''.join(book_card(b, authors, subjects) for b in rows)}</div>
  </section>""")
    n_books = len(books)
    n_authors = len(catalog["authors"])
    body = f"""{head(title, desc, depth)}
<body>
{header(depth)}
<main id="content" class="wrap">
  <section class="hero">
    <h1>Public-domain books</h1>
    <p class="lede">{n_books} public-domain books by {n_authors} authors. Open Library. Browse only.</p>
  </section>
  <div class="find">
    <label for="find">Search the catalog</label>
    <input id="find" data-find type="search" placeholder="Austen, Douglass, a title…" autocomplete="off">
    <ul id="find-results" class="find-results" hidden></ul>
  </div>
  <div id="shelves">
  {''.join(shelf_html)}
  </div>
  <hr class="rule">
  <h2 class="shelf-label">Subjects</h2>
  <ul class="subjects">{subject_bits}</ul>
</main>
{footer(depth)}
"""
    write(ROOT / "index.html", body)
    rows = [{"t": b["title"], "a": authors[b["author"]]["name"], "s": b["slug"]} for b in books]
    (ROOT / "search.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    print("HOME", body.count('class="card"'), "cards")


def main():
    catalog = json.loads(CATALOG.read_text())
    assert catalog["brand"] == BRAND
    authors = {a["slug"]: a for a in catalog["authors"]}
    subjects = {s["slug"]: s for s in catalog["subjects"]}
    for b in catalog["books"]:
        if not b.get("pd", False):
            raise SystemExit(f"refusing non-pd book {b['slug']}")
        if not re.fullmatch(r"OL\d+W", b["ol_id"]):
            raise SystemExit(f"bad ol id {b['ol_id']}")
        if f"/books/" in b["ol_url"] or b["ol_id"] in b["slug"]:
            raise SystemExit("ol id leaked into path-ish data")
        g = b["gutenberg_url"]
        if not re.fullmatch(r"https://www\.gutenberg\.org/ebooks/\d+", g):
            raise SystemExit(f"bad gutenberg url {g}")
    # drop generated html first
    for folder in ("books", "authors", "subjects"):
        p = ROOT / folder
        if p.exists():
            for f in p.glob("*/*"):
                if f.is_file():
                    f.unlink()
    page_home(catalog, authors, subjects)
    from collections import defaultdict
    by_author = defaultdict(list)
    by_subject = defaultdict(list)
    for b in catalog["books"]:
        by_author[b["author"]].append(b)
        for slug in b["subjects"]:
            by_subject[slug].append(b)
    for b in catalog["books"]:
        page_book(b, authors, subjects, by_author, by_subject)
    used_authors = []
    for a in catalog["authors"]:
        mine = [b for b in catalog["books"] if b["author"] == a["slug"]]
        if not mine:
            continue
        used_authors.append(a)
        page_author(a, mine, subjects)
    for s in catalog["subjects"]:
        mine = [b for b in catalog["books"] if s["slug"] in b["subjects"]]
        if not mine:
            raise SystemExit(f"empty subject {s['slug']}")
        page_subject(s, mine, authors)
    print(f"pages: 1 home, {len(catalog['books'])} books, {len(used_authors)} authors, {len(catalog['subjects'])} subjects")

if __name__ == "__main__":
    import sys
    if "--home-only" in sys.argv:
        catalog = json.loads(CATALOG.read_text())
        authors = {a["slug"]: a for a in catalog["authors"]}
        subjects = {s["slug"]: s for s in catalog["subjects"]}
        page_home(catalog, authors, subjects)
    else:
        main()
