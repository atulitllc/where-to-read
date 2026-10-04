# Where to Read

A static catalog of public-domain books. Reading happens on Open Library. This site does not host the books.

- Covers are hotlinked from `covers.openlibrary.org` and are not stored in this repository.
- Project Gutenberg links point only at `https://www.gutenberg.org/ebooks/ID`.
- Every HTML page sends `noindex` and a relative canonical of `./`.
- Open Library work ids are printed on book pages. They are not part of the URL.
- Book schema uses a relative `url` of `./`. `sameAs` lists the Open Library work and the Gutenberg landing page only.

Rebuild pages with `python3 tools/build_site.py` after `data/catalog.json` exists. `tools/enrich.py` refreshes Open Library ids with one lookup per known title. `tools/assemble_catalog.py` can extend the catalog from a local Gutenberg metadata export and an Open Library id map. Do not point either tool at ebook files.
