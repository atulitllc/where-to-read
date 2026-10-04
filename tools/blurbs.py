#!/usr/bin/env python3
"""Stored blurbs. The lead × shelf template generator has been removed.

Featured books keep a handwritten blurb. Every other blurb is already written
on the catalog record (a public description, restated, or the book's own
subject headings). Build does not call a filler. History is not generated.
"""


def apply_blurbs(*_args, **_kwargs):
    raise SystemExit(
        "apply_blurbs is disabled. Blurbs are stored per book and are not filled from a template."
    )


def make_blurb(*_args, **_kwargs):
    raise SystemExit("make_blurb is disabled. Blurbs are stored per book.")


def history_copy(*_args, **_kwargs):
    raise SystemExit("history templates are disabled and are not emitted.")
