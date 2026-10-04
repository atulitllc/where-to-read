# Where to Read

A static catalog of public-domain books. Reading happens on Open Library. This site does not host the books.

- Covers are hotlinked from `covers.openlibrary.org` and are not stored in this repository.
- Project Gutenberg links point only at `https://www.gutenberg.org/ebooks/ID`.
- Every HTML page sends `noindex`. Canonical, `og:url`, the home WebSite `url`, and each page schema `url` are absolute `https://booksthere.com/...` addresses with a trailing slash. Nothing points at github.io or www.
- Open Library work ids are printed on book pages. They are not part of the URL.
- Book schema `url` is the apex catalog page, such as `https://booksthere.com/books/pride-and-prejudice/`. `sameAs` lists the Open Library work and the Gutenberg landing page only.

Rebuild pages with `python3 tools/build_site.py` after `data/catalog.json` exists. `tools/enrich.py` refreshes Open Library ids with one lookup per known title. `tools/assemble_catalog.py` can extend the catalog from a local Gutenberg metadata export and an Open Library id map. Do not point either tool at ebook files.
