#!/usr/bin/env python3
"""Static pages for Where to Read. No book files. Covers are hotlinked."""
import html
import json
import re
from pathlib import Path

from blurb_gate import check_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"
BRAND = "Where to Read"
# Sitewide noindex is off. The catalog is served at the booksthere.com apex.
# Empty-blurb book pages still pass thin=True and keep their own robots noindex.
# Do not drop that per-page tag, and do not list those URLs in the sitemap.
SITEWIDE_NOINDEX = False
# One origin for every public URL the generators emit. Apex, https, no www.
SITE_ORIGIN = "https://booksthere.com"
FORBIDDEN = re.compile(r"\b(pdf|epub|mobi|download|free ebook)\b", re.I)


def absolute_url(site_path=""):
    """Absolute apex URL, keeping the trailing slash the page already uses.

    Home is https://booksthere.com/ even when the file is index.html.
    """
    site_path = (site_path or "").strip().strip("/")
    if site_path == "index.html" or site_path.endswith("/index.html"):
        site_path = site_path[: -len("index.html")].strip("/")
    if not site_path:
        url = SITE_ORIGIN + "/"
    else:
        url = f"{SITE_ORIGIN}/{site_path}/"
    if (
        not url.startswith(SITE_ORIGIN + "/")
        or "github.io" in url
        or "://www." in url
        or url.startswith("http://")
    ):
        raise SystemExit(f"refusing non-apex URL {url}")
    return url


def json_ld(obj):
    payload = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    return '<script type="application/ld+json">' + payload + "</script>"

def has_note(book):
    return bool((book.get("blurb") or "").strip())

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

def head(title, description, depth, extra="", thin=False, path=""):
    prefix = "../" * depth
    # Sitewide noindex is off. An empty-blurb book page is noindex on its own,
    # so the tag remains on that thin page after the sitewide flag is turned off.
    meta_bits = []
    if thin:
        meta_bits.append("<!-- empty-blurb noindex -->")
    if SITEWIDE_NOINDEX or thin:
        meta_bits.append('<meta name="robots" content="noindex">')
    meta_block = ("\n".join(meta_bits) + "\n") if meta_bits else ""
    url = absolute_url(path)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{meta_block}<link rel="canonical" href="{esc(url)}">
<meta property="og:url" content="{esc(url)}">
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
    prefix = "../" * depth
    return f"""<footer class="colophon wrap">
  <p>Where to Read is a catalog of public-domain books. You read them on Open Library. This site does not host copyrighted books.</p>
  <p>Records are from <a href="https://openlibrary.org/" target="_blank" rel="noopener noreferrer">Open Library</a>. Cover images, when a record has one, are loaded from covers.openlibrary.org and are not stored here. Project Gutenberg links open that book’s landing page only. <a href="{prefix}about/">About this catalog</a>.</p>
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
    page = absolute_url(f"books/{book['slug']}")
    schema = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": book["title"],
        "author": {
            "@type": "Person",
            "name": author["name"],
            "url": absolute_url(f"authors/{author['slug']}"),
        },
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "Open Library",
            "value": book["ol_id"],
        },
        "sameAs": same,
        "url": page,
    }
    # Book.url is this catalog page on the apex. sameAs keeps the Open Library work.
    if schema["url"] == book["ol_url"] or schema["url"] != page:
        raise SystemExit(f"Book.url must be the apex catalog page for {book['slug']}")
    if not schema["url"].startswith(f"{SITE_ORIGIN}/books/") or schema["author"]["url"] != absolute_url(f"authors/{author['slug']}"):
        raise SystemExit(f"schema url left the apex for {book['slug']}")
    if book.get("year"):
        schema["datePublished"] = str(book["year"])
    if book.get("cover_i"):
        schema["image"] = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
    extra = json_ld(schema)
    same_author = pick_related(book, [b for b in by_author.get(book["author"], []) if has_note(b)])
    primary = book["subjects"][0]
    same_subject = pick_related(
        book,
        [b for b in by_subject.get(primary, []) if b["author"] != book["author"] and has_note(b)],
    )
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
    blurb_html = (
        f'<p class="blurb">{esc(book["blurb"])}</p>'
        if (book.get("blurb") or "").strip()
        else ""
    )
    body = f"""{head(title, desc, depth, extra, thin=not has_note(book), path=f"books/{book['slug']}")}
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
        {blurb_html}
      </div>
    </div>
    <div class="book-details">
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
    listed = [b for b in books if has_note(b)]
    rails = home_rails(listed, {author["slug"]: author}, subjects, prefix=prefix)
    shelf = f'<hr class="rule">\n  <div class="shelf">{rails}</div>' if listed else ""
    body = f"""{head(title, desc, depth, path=f"authors/{author['slug']}")}
<body>
{header(depth)}
<main id="content" class="wrap detail-wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">Where to Read</a> <span aria-hidden="true">/</span> <span>{esc(author['name'])}</span></nav>
  <p class="kicker">Author</p>
  <h1>{esc(author['name'])}</h1>
  <p class="lede">{esc(author['intro'])}</p>
  {shelf}
</main>
{footer(depth)}
"""
    write(ROOT / "authors" / author["slug"] / "index.html", body)

def page_subject(subject, books, authors, subjects):
    depth = 2
    prefix = "../../"
    title = f"{subject['name']} books | {BRAND}"
    desc = f"Public-domain {subject['name'].lower()} books in this catalog. Read them on Open Library. This site does not host copyrighted books."
    listed = [b for b in books if has_note(b)]
    rails = home_rails(listed, authors, subjects, prefix=prefix)
    shelf = f'<hr class="rule">\n  <div class="shelf">{rails}</div>' if listed else ""
    body = f"""{head(title, desc, depth, path=f"subjects/{subject['slug']}")}
<body>
{header(depth)}
<main id="content" class="wrap detail-wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">Where to Read</a> <span aria-hidden="true">/</span> <span>{esc(subject['name'])}</span></nav>
  <p class="kicker">Subject</p>
  <h1>{esc(subject['name'])}</h1>
  <p class="lede">{esc(subject['intro'])}</p>
  {shelf}
</main>
{footer(depth)}
"""
    write(ROOT / "subjects" / subject["slug"] / "index.html", body)

def book_card(b, authors, subjects, prefix=""):
    author = authors[b["author"]]
    year = f"{b['year']} · " if b.get("year") else ""
    depth = prefix.count("../")
    thumb = f'<span class="thumb">{cover_html(b)}</span>'
    blurb_html = (
        f'<p class="blurb">{esc(b["blurb"])}</p>'
        if (b.get("blurb") or "").strip()
        else ""
    )
    return f"""<article class="card">
        <a href="{prefix}books/{b['slug']}/">{thumb}</a>
        <div>
          <h2><a href="{prefix}books/{b['slug']}/">{esc(b['title'])}</a></h2>
          <p class="by">by <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a></p>
          <p class="meta">{year}{subject_links(b, subjects, depth)}</p>
          {blurb_html}
        </div>
      </article>"""


def home_rails(books, authors, subjects, prefix="", per_row=9):
    """One wooden board per row — wrap stays CSS-side for narrow viewports."""
    if not books:
        return ""
    chunks = [books[i:i + per_row] for i in range(0, len(books), per_row)]
    return "".join(
        f'<div class="home-rail">{"".join(book_card(b, authors, subjects, prefix) for b in chunk)}</div>'
        for chunk in chunks
    )


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
        if not b or slug in seen or not has_note(b):
            continue
        if subject and subject not in b["subjects"]:
            continue
        chosen.append(b)
        seen.add(slug)
        if len(chosen) == limit:
            return chosen
    pool = [b for b in books if has_note(b) and b["slug"] not in seen and (not subject or subject in b["subjects"])]
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
    shelves = [(label, slug, pick_books(books, seeds, 9, subject=slug)) for label, slug, seeds in READ_SHELVES]
    shown = len(top) + sum(len(rows) for _l, _s, rows in shelves)
    if shown > 80:
        raise SystemExit(f"home card cap {shown}")
    shelf_html = [f"""<section class="shelf" aria-labelledby="top-read">
    <div class="shelf-head"><h2 id="top-read" class="shelf-label">Top Read</h2></div>
    {home_rails(top, authors, subjects)}
  </section>"""]
    for label, slug, rows in shelves:
        shelf_html.append(f"""<section class="shelf" aria-labelledby="shelf-{esc(slug)}">
    <div class="shelf-head"><h2 id="shelf-{esc(slug)}" class="shelf-label">{esc(label)}</h2><a class="see-all" href="subjects/{esc(slug)}/">See all</a></div>
    {home_rails(rows, authors, subjects)}
  </section>""")
    n_books = len(books)
    n_authors = len(catalog["authors"])
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": BRAND,
        "url": absolute_url(""),
    }
    if website["url"] != SITE_ORIGIN + "/":
        raise SystemExit("WebSite url must be the apex home URL")
    body = f"""{head(title, desc, depth, json_ld(website), path="")}
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
  <nav class="subject-nav" aria-label="Subjects">
    <ul class="subjects">{subject_bits}</ul>
  </nav>
  <div id="shelves">
  {''.join(shelf_html)}
  </div>
</main>
{footer(depth)}
"""
    write(ROOT / "index.html", body)
    rows = [{"t": b["title"], "a": authors[b["author"]]["name"], "s": b["slug"]} for b in books if has_note(b)]
    (ROOT / "search.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    print("HOME", body.count('class="card"'), "cards")


def page_about():
    depth = 1
    title = f"About | {BRAND}"
    desc = "What this catalog is. Public-domain books, read on Open Library. This site does not host the books."
    body = f"""{head(title, desc, depth, path="about")}
<body>
{header(depth)}
<main id="content" class="wrap detail-wrap">
  <p class="kicker">Catalog notes</p>
  <h1>A shelf, not a library.</h1>
  <p class="lede">Where to Read is a static catalog of public-domain books. It tells you where a text can be read. It does not host the books.</p>
  <h2 class="shelf-label">What you will not find here</h2>
  <p>No ebook files, and no copy of a copyrighted book. Each title links out to its Open Library work and, when there is a landing page, to Project Gutenberg. Those links leave this site.</p>
  <h2 class="shelf-label">Where the facts come from</h2>
  <p>The title, the author, and any year printed on a card come from the catalog record. A year is shown only when that record already has one, and never past 1928. A featured book keeps a handwritten note. Any other note is a sentence rewritten from a public description of that book. Where no such description was found, the card has no note: that book page is noindex on its own, and the title is left off the author and subject shelves. Notes do not carry catalog ids.</p>
  <h2 class="shelf-label">Covers and indexing</h2>
  <p>Cover images, when a record has one, are loaded from covers.openlibrary.org. They are not stored here. A book page with no note sends its own noindex robots tag. Every other page is open to indexing. Each canonical URL is the absolute address of that page on https://booksthere.com/, with the trailing slash. The sitemap lists those indexable addresses and leaves the empty-note book pages out.</p>
</main>
{footer(depth)}
"""
    write(ROOT / "about" / "index.html", body)


def indexable_paths(catalog, used_authors):
    """Home, about, every author and subject hub, and book pages that have a note.

    Empty-blurb book URLs are indexable nowhere: they stay noindex and stay out.
    """
    paths = ["", "about"]
    for subject in catalog["subjects"]:
        paths.append(f"subjects/{subject['slug']}")
    for author in used_authors:
        paths.append(f"authors/{author['slug']}")
    for book in catalog["books"]:
        if has_note(book):
            paths.append(f"books/{book['slug']}")
    return paths


def write_sitemap(paths):
    locs = []
    seen = set()
    for site_path in paths:
        url = absolute_url(site_path)
        if url in seen:
            raise SystemExit(f"duplicate sitemap url {url}")
        seen.add(url)
        locs.append(f"  <url>\n    <loc>{esc(url)}</loc>\n  </url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(locs)
        + "\n</urlset>\n"
    )
    write(ROOT / "sitemap.xml", xml)
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE_ORIGIN}/sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(robots)
    return locs


def main():
    catalog = json.loads(CATALOG.read_text())
    check_catalog(catalog)
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
        page_subject(s, mine, authors, subjects)
    page_about()
    paths = indexable_paths(catalog, used_authors)
    write_sitemap(paths)
    assert_empty_blurbs_unlinked(catalog)
    assert_apex_urls(catalog)
    n_empty = sum(1 for b in catalog["books"] if not has_note(b))
    n_noted = len(catalog["books"]) - n_empty
    print(
        f"pages: 1 home, {len(catalog['books'])} books, {len(used_authors)} authors, "
        f"{len(catalog['subjects'])} subjects, about"
    )
    print(
        f"sitemap: {len(paths)} indexable urls; books with notes {n_noted}; "
        f"empty-blurb books excluded {n_empty}"
    )


def assert_apex_urls(catalog):
    """Canonical, og:url, WebSite url, and page schema url stay on the apex."""
    canonical_re = re.compile(r'<link rel="canonical" href="([^"]*)">')
    og_re = re.compile(r'<meta property="og:url" content="([^"]*)">')
    schema_url_re = re.compile(r'"url": "([^"]*)"')
    html_files = [ROOT / "index.html", ROOT / "about" / "index.html"]
    for folder in ("books", "authors", "subjects"):
        html_files.extend((ROOT / folder).glob("*/index.html"))
    if not html_files:
        raise SystemExit("no pages to check")
    empty = {
        b["slug"]
        for b in catalog["books"]
        if not (b.get("blurb") or "").strip()
    }
    for path in html_files:
        rel = path.relative_to(ROOT).as_posix()
        if rel == "index.html":
            expected = absolute_url("")
        elif rel.endswith("/index.html"):
            expected = absolute_url(rel[: -len("/index.html")])
        else:
            raise SystemExit(f"unexpected page {rel}")
        text = path.read_text()
        is_empty_book = rel.startswith("books/") and rel.split("/")[1] in empty
        has_robots = 'name="robots" content="noindex"' in text
        has_thin_mark = "<!-- empty-blurb noindex -->" in text
        if is_empty_book:
            if not has_robots or not has_thin_mark:
                raise SystemExit(f"empty-blurb page lost its own noindex {rel}")
        else:
            if has_robots or has_thin_mark:
                raise SystemExit(f"indexable page still noindex {rel}")
        if SITEWIDE_NOINDEX:
            raise SystemExit("sitewide noindex is still on")
        cans = canonical_re.findall(text)
        ogs = og_re.findall(text)
        if cans != [expected] or ogs != [expected]:
            raise SystemExit(f"canonical/og:url mismatch in {rel}: {cans} {ogs}")
        if 'href="./"' in text or "github.io" in text or "www.booksthere.com" in text:
            raise SystemExit(f"relative or non-apex URL in {rel}")
        for url in schema_url_re.findall(text):
            if not url.startswith(SITE_ORIGIN + "/") or "github.io" in url or "://www." in url:
                raise SystemExit(f"schema url left the apex in {rel}: {url}")
    home = (ROOT / "index.html").read_text()
    if f'"@type": "WebSite"' not in home or f'"url": "{SITE_ORIGIN}/"' not in home:
        raise SystemExit("home WebSite url is not the apex")
    pride = ROOT / "books" / "pride-and-prejudice" / "index.html"
    pride_text = pride.read_text()
    pride_url = absolute_url("books/pride-and-prejudice")
    if pride_url not in pride_text or 'href="./"' in pride_text:
        raise SystemExit("Pride and Prejudice is missing its apex URL")
    if 'name="robots" content="noindex"' in pride_text or "<!-- empty-blurb noindex -->" in pride_text:
        raise SystemExit("Pride and Prejudice is still noindex")
    if "<span class=\"brand-word\">books<span class=\"brand-accent\">there</span></span>" not in pride_text:
        raise SystemExit("wordmark changed")
    assert_sitemap(catalog, empty)


def assert_sitemap(catalog, empty):
    """Sitemap lists indexable apex URLs only. robots.txt names that sitemap."""
    robots = (ROOT / "robots.txt").read_text()
    sitemap_line = f"Sitemap: {SITE_ORIGIN}/sitemap.xml"
    if sitemap_line not in robots.splitlines():
        raise SystemExit(f"robots.txt does not name {sitemap_line}")
    if "github.io" in robots or "www.booksthere.com" in robots or "http://" in robots:
        raise SystemExit("robots.txt names a non-apex host")
    xml = (ROOT / "sitemap.xml").read_text()
    if "github.io" in xml or "www.booksthere.com" in xml:
        raise SystemExit("sitemap left the https apex")
    # The sitemap namespace itself is the http URI from the sitemap protocol.
    # Every <loc> still has to be the https apex.
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    if any(url.startswith("http://") for url in locs):
        raise SystemExit("sitemap loc left https")
    if len(locs) != len(set(locs)):
        raise SystemExit("duplicate sitemap urls")
    expected = set()
    expected.add(absolute_url(""))
    expected.add(absolute_url("about"))
    for subject in catalog["subjects"]:
        expected.add(absolute_url(f"subjects/{subject['slug']}"))
    for author in catalog["authors"]:
        # page_author skips an author with no books. Every catalog author has one.
        expected.add(absolute_url(f"authors/{author['slug']}"))
    noted = 0
    for book in catalog["books"]:
        url = absolute_url(f"books/{book['slug']}")
        if book["slug"] in empty:
            if url in locs:
                raise SystemExit(f"empty-blurb book in sitemap: {book['slug']}")
            continue
        noted += 1
        expected.add(url)
    if set(locs) != expected:
        missing = sorted(expected - set(locs))[:5]
        extra = sorted(set(locs) - expected)[:5]
        raise SystemExit(f"sitemap urls mismatch missing={missing} extra={extra}")
    pride = absolute_url("books/pride-and-prejudice")
    if pride not in locs:
        raise SystemExit("Pride and Prejudice missing from sitemap")
    if noted + len(empty) != len(catalog["books"]):
        raise SystemExit("note/empty split does not cover the catalog")
    for url in locs:
        if not url.startswith(SITE_ORIGIN + "/") or not url.endswith("/"):
            raise SystemExit(f"sitemap url is not an apex path {url}")


def assert_empty_blurbs_unlinked(catalog):
    """Fail if an empty-blurb book is linked from a hub, related list, or search."""
    empty = {
        b["slug"]
        for b in catalog["books"]
        if not (b.get("blurb") or "").strip()
    }
    rows = json.loads((ROOT / "search.json").read_text())
    for row in rows:
        slug = row.get("s") or ""
        if slug in empty:
            raise SystemExit(f"empty-blurb book in search.json: {slug}")
    hrefs = re.compile(r"books/([a-z0-9-]+)/")
    hubs = [ROOT / "index.html", ROOT / "about" / "index.html", ROOT / "sitemap.xml"]
    for folder in ("authors", "subjects", "books"):
        hubs.extend((ROOT / folder).glob("*/*"))
    for path in hubs:
        if not path.is_file():
            continue
        # A book page names itself in canonical, og:url, and schema url.
        # That is not an inbound link. Any other books/slug/ still counts.
        own = ""
        parts = path.relative_to(ROOT).parts
        if len(parts) == 3 and parts[0] == "books" and parts[2] == "index.html":
            own = parts[1]
        for slug in hrefs.findall(path.read_text(errors="ignore")):
            if slug == own:
                continue
            if slug in empty:
                rel = path.relative_to(ROOT)
                raise SystemExit(f"empty-blurb book linked from {rel}: {slug}")

if __name__ == "__main__":
    import sys
    if "--home-only" in sys.argv:
        catalog = json.loads(CATALOG.read_text())
        authors = {a["slug"]: a for a in catalog["authors"]}
        subjects = {s["slug"]: s for s in catalog["subjects"]}
        page_home(catalog, authors, subjects)
    else:
        main()
