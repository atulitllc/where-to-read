#!/usr/bin/env python3
"""Static pages for Where to Read. No book files. Covers are hotlinked."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalog.json"
BRAND = "Where to Read"
FORBIDDEN = re.compile(r"\b(pdf|epub|mobi|download|free ebook)\b", re.I)

def esc(s):
    return html.escape(s if s is not None else "", quote=True)

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
    return """<svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
  <path d="M5 23c2.4-1.5 5-1.7 7.6-1 1.3-1.5 3.6-2.1 6-1.6 2.1.4 3.8 1.5 6 1.6V8.6c-2.1-.4-4-1.5-6.3-1.7-2.2-.2-4.5.3-5.8 1.7C10.8 7 8.2 6.8 5 8.2V23z" fill="none" stroke="currentColor" stroke-width="1.6"/>
  <path d="M16 8.4v13.2" stroke="currentColor" stroke-width="1.4"/>
</svg>"""

def header(depth):
    prefix = "../" * depth
    return f"""<a class="skip" href="#content">Skip to content</a>
<header class="topbar">
  <div class="wrap topbar-inner">
    <a class="brand" href="{prefix}">{brand_svg()}Where to Read</a>
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
  <p>Records are from <a href="https://openlibrary.org/">Open Library</a>. Cover images, when a record has one, are loaded from covers.openlibrary.org and are not stored here. Project Gutenberg links open that book’s landing page only.</p>
</footer>
<script src="{prefix}js/theme.js"></script>
</body>
</html>
""".replace("{prefix}", "../" * depth)

def cover_html(book, large=False):
    alt = f"Cover of {book['title']} from Open Library"
    if book.get("cover_i"):
        src = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
        return f'<img class="cover" src="{esc(src)}" alt="{esc(alt)}" width="330" height="500">'
    return f'<div class="cover-fallback" role="img" aria-label="{esc(alt)}">{esc(book["title"])}</div>'

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

def page_book(book, authors, subjects):
    author = authors[book["author"]]
    depth = 2
    prefix = "../../"
    title = f"{book['title']} by {author['name']} | {BRAND}"
    desc = f"A catalog entry for the public-domain book {book['title']} by {author['name']}. Read it on Open Library. This site does not host copyrighted books."
    year = f"{book['year']} · " if book.get("year") else ""
    read_li = ""
    if book.get("read_url"):
        read_li = f'<li><a href="{esc(book["read_url"])}">Read or borrow on Open Library</a></li>'
    same = [book["ol_url"], book["gutenberg_url"]]
    if book.get("read_url"):
        same.append(book["read_url"])
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
        "url": book["ol_url"],
    }
    if book.get("year"):
        schema["datePublished"] = str(book["year"])
    if book.get("cover_i"):
        schema["image"] = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-L.jpg"
    extra = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c") + "</script>"
    body = f"""{head(title, desc, depth, extra)}
<body>
{header(depth)}
<main id="content" class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb">
    <a href="{prefix}">Where to Read</a>
    <span aria-hidden="true">/</span>
    <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a>
    <span aria-hidden="true">/</span>
    <span>{esc(book['title'])}</span>
  </nav>
  <article class="book">
    {cover_html(book)}
    <div>
      <p class="kicker">Public-domain book</p>
      <h1>{esc(book['title'])}</h1>
      <p class="by">by <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a></p>
      <p class="meta">{year}{subject_links(book, subjects, depth)}</p>
      <p class="ol-id">Open Library {esc(book['ol_id'])}</p>
      <p class="blurb">{esc(book['blurb'])}</p>
      <h2 class="shelf-label">Where to read it</h2>
      <ul class="where">
        <li><a href="{esc(book['ol_url'])}">Open Library record</a></li>
        {read_li}
        <li><a href="{esc(book['gutenberg_url'])}">Project Gutenberg page</a></li>
      </ul>
      <p class="note">Open Library hosts the reading view. Some editions open in the browser; others ask you to borrow. Project Gutenberg links in this catalog open the book’s page, not a file kept here.</p>
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
        items.append(f"""<article>
          <h2><a href="{prefix}books/{b['slug']}/">{esc(b['title'])}</a></h2>
          <p class="meta">{(str(b['year']) + ' · ') if b.get('year') else ''}{subject_links(b, subjects, depth)}</p>
          <p>{esc(b['blurb'])}</p>
        </article>""")
    body = f"""{head(title, desc, depth)}
<body>
{header(depth)}
<main id="content" class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">Where to Read</a> <span aria-hidden="true">/</span> <span>{esc(author['name'])}</span></nav>
  <p class="kicker">Author</p>
  <h1>{esc(author['name'])}</h1>
  <p class="lede">{esc(author['intro'])}</p>
  <hr class="rule">
  <div class="book-list">{''.join(items)}</div>
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
        items.append(f"""<article>
          <h2><a href="{prefix}books/{b['slug']}/">{esc(b['title'])}</a></h2>
          <p class="by">by <a href="{prefix}authors/{author['slug']}/">{esc(author['name'])}</a></p>
          <p>{esc(b['blurb'])}</p>
        </article>""")
    body = f"""{head(title, desc, depth)}
<body>
{header(depth)}
<main id="content" class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{prefix}">Where to Read</a> <span aria-hidden="true">/</span> <span>{esc(subject['name'])}</span></nav>
  <p class="kicker">Subject</p>
  <h1>{esc(subject['name'])}</h1>
  <p class="lede">{esc(subject['intro'])}</p>
  <hr class="rule">
  <div class="book-list">{''.join(items)}</div>
</main>
{footer(depth)}
"""
    write(ROOT / "subjects" / subject["slug"] / "index.html", body)

def page_home(catalog, authors, subjects):
    books = catalog["books"]
    depth = 0
    title = f"Public-domain books | {BRAND}"
    desc = "A catalog of public-domain books you can read on Open Library. This site does not host copyrighted books."
    subject_bits = "".join(
        f'<li><a href="subjects/{esc(s["slug"])}/">{esc(s["name"])}</a></li>' for s in catalog["subjects"]
    )
    author_bits = "".join(
        f'<li><a href="authors/{esc(a["slug"])}/">{esc(a["name"])}</a></li>' for a in catalog["authors"]
    )
    cards = []
    for b in books:
        author = authors[b["author"]]
        hay = esc(f"{b['title']} {author['name']}")
        year = f"{b['year']} · " if b.get("year") else ""
        cards.append(f"""<article class="card" data-card="{hay}">
        <a href="books/{b['slug']}/">{cover_html(b)}</a>
        <div>
          <h2><a href="books/{b['slug']}/">{esc(b['title'])}</a></h2>
          <p class="by">by <a href="authors/{author['slug']}/">{esc(author['name'])}</a></p>
          <p class="meta">{year}{subject_links(b, subjects, 0)}</p>
          <p class="blurb">{esc(b['blurb'])}</p>
        </div>
      </article>""")
    body = f"""{head(title, desc, depth)}
<body>
{header(depth)}
<main id="content" class="wrap">
  <section class="hero">
    <p class="kicker">A reading catalog</p>
    <h1>Public-domain books for a quiet evening</h1>
    <p class="lede">A lamp-lit shelf of older books, with the reading itself on Open Library.</p>
    <p class="fine">Where to Read keeps a catalog only. It does not host copyrighted books. Cover images are requested from Open Library when you open a page.</p>
  </section>
  <hr class="rule">
  <h2 class="shelf-label">Subjects</h2>
  <ul class="subjects">{subject_bits}</ul>
  <hr class="rule">
  <h2 class="shelf-label">The shelf</h2>
  <div class="find">
    <label for="find">Find a title or author on this page</label>
    <input id="find" data-find type="search" placeholder="Austen, Gatsby, Douglass…">
  </div>
  <div class="catalog">{''.join(cards)}</div>
  <hr class="rule">
  <h2 class="shelf-label">Authors</h2>
  <ul class="author-index">{author_bits}</ul>
</main>
{footer(depth)}
"""
    write(ROOT / "index.html", body)

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
    for b in catalog["books"]:
        page_book(b, authors, subjects)
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
    main()
