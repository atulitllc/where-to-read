#!/usr/bin/env python3
"""Fail the build if a stock year clause, an old lead, or a subject-heading frame is back.

The patterns below are detectors only. Nothing in this module fills a blurb.
An empty note is allowed. A featured book still needs its handwritten note.
"""
import re
import unicodedata

# Fixed wording from the retired LEADS list and the stock year/shelf sentences.
# Short function words are intentionally not listed; these are the repeated frames.
FORBIDDEN_SUBSTRINGS = (
    "and all this note will claim",
    "one sturdy fact",
    "no need to invent a plot",
    "does not ask this page",
    "The honest line on",
    "Nothing fancier than",
    "The concrete end of",
    "No scene list is required",
    "Where a plot summary would wander",
    "Name the subject as",
    "not a puzzle to be solved here",
    "From the first glance",
    "A plain note on",
    "contributes to its shelf",
    "doing the real work",
    "as narrow as its subject",
    "one subject worth naming",
    "is enough: it is about",
    "The topic inside",
    "answers to the subject",
    "For a first description",
    "The work in hand is",
    "and stops there",
    "the subject it earns",
    "Before any story is guessed",
    "filed by one phrase",
    "The useful fact in",
    "keeps to the subject",
    "does not pretend otherwise",
    "Nothing here retells",
    "best introduced through",
    "keeps its attention on",
    "at catalog length",
    "the subject comes first",
    "The subject line that fits",
    "can be summed up as",
    "and then stop",
    "does its work on the subject",
    "Look past the binding",
    "whose brief is",
    "a later reader brings",
    "The only summary",
    "comes into focus",
    "There is a plain way to say",
    "rather than a plot",
    "No year was invented",
    "was already the one on the book",
    "not one filled in to plug a gap",
    "The printing year we actually have",
    "sits with the title as a real date",
    "The year already recorded is",
    "because that year was already known",
    "The known year is",
    "Leave the date as",
    "which was already there",
    "Beyond the subject, the title contributes the color",
    "is the writer, and the book sits on",
    "sits on the",
    "on the subject of",
    "Another way to place",
    "easier to shelve",
    "The shelf decision for",
    "neighbored with other books",
    "life and the shelf",
    "Nothing below invents",
    "does not need a synopsis",
    "This note stays outside the plot",
    "the life dates and the shelf",
    "Nothing in this paragraph happens inside",
    "the form does the shelving",
    "without a later date being invented",
    "left unrehearsed here",
)

# "{title} is {kind} about {about}." with the old kind vocabulary.
OLD_KIND = (
    r"a book of verse|a play|a collection of short stories|a book of letters|"
    r"a book of essays|a work of philosophy|a memoir|a biography|a travel narrative|"
    r"a science book|a religious work|a humorous book|a mystery|a gothic novel|"
    r"a romance|a science-fiction story|a children's fantasy|a fantasy|"
    r"an adventure novel|a children's novel|a children's book|a historical novel|"
    r"a novel|a history|a literary work|a children's fantasy"
)
OLD_LEAD = re.compile(
    rf"\bis (?:{OLD_KIND}) about\b",
    re.I,
)
FUTURE_YEAR = re.compile(r"\b(19[3-9]\d|20\d\d)\b")
CATALOG_ID = re.compile(
    r"\bOL\d+W\b|\b(open library|wikipedia|booksthere\.com|project gutenberg)\b",
    re.I,
)
MONTHS = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)
# Past participles and -ed adjectives that do not make a sentence on their own.
_ED_NOT_FINITE = {
    "illustrated", "gathered", "based", "titled", "entitled", "called", "named",
    "known", "written", "starred", "famed", "alleged", "detailed", "related",
    "noted", "celebrated", "renowned", "united", "supposed", "sacred", "wicked",
    "naked", "aged", "beloved", "armed", "wounded", "unexpected", "distinguished",
    "unfinished", "unrecognized", "limited", "hundred", "kindred", "wretched",
    "rugged", "learned", "blessed", "cursed", "concerned", "tired", "inspired",
    "determined", "complicated", "interested", "advanced", "marked", "mixed",
    "fixed", "closed", "supposed", "so-called", "so called", "untitled",
}
_AUX = re.compile(
    r"\b(is|are|was|were|be|been|being|am|has|have|had|do|does|did|"
    r"will|would|can|could|may|might|shall|should|must)\b",
    re.I,
)
_FINITE = re.compile(
    r"\b("
    r"says|said|tells|told|writes|wrote|goes|went|comes|came|becomes|became|"
    r"sees|saw|makes|made|takes|took|gives|gave|gets|got|finds|found|"
    r"leaves|left|keeps|kept|knows|knew|thinks|thought|feels|felt|"
    r"begins|began|brings|brought|runs|ran|stands|stood|grows|grew|"
    r"hears|heard|leads|led|loses|lost|meets|met|pays|paid|reads|"
    r"sends|sent|speaks|spoke|teaches|taught|wins|won|draws|drew|"
    r"falls|fell|rises|rose|sits|sat|holds|held|lets|means|meant|"
    r"seems|appears|includes|contains|follows|describes|concerns|"
    r"opens|presents|offers|shows|features|focuses|covers|spans|"
    r"records|relates|introduces|uses|argues|claims|explains|defines|"
    r"discusses|surveys|outlines|remains|serves|lives|dies|died|"
    r"parodies|credits|stars|disappears|assembles|derives|alleges|allege|"
    r"comprises|reflects|refers|recounts|recount|depicts|portrays|narrates|"
    r"chronicles|traces|explores|examines|combines|publishes|collects|"
    r"translates|adapts|calls|considers|regards|defends|attempts|"
    r"wishes|earns|produces|attributes|looks|arises|builds|built|creates|"
    r"forms|centres|centers|revolves|deals|dealt|turns|turned|"
    r"continues|receives|returns|marries|visits|sails|fights|fought|"
    r"grapples|entices|enticed|converts|preaches|develops|compiles|"
    r"take|takes|reacquaints|re-acquaints|put|puts|set|sets|"
    r"say|tell|write|go|come|see|make|give|get|find|leave|keep|know|"
    r"think|feel|begin|bring|run|stand|grow|hear|lead|lose|meet|pay|"
    r"send|speak|teach|win|draw|fall|rise|sit|hold|let|mean|seem|"
    r"appear|include|contain|follow|describe|concern|open|present|"
    r"offer|show|feature|focus|cover|span|record|relate|introduce|"
    r"use|argue|claim|explain|define|discuss|survey|outline|remain|"
    r"serve|live|die|parody|credit|star|disappear|assemble|derive|"
    r"comprise|reflect|refer|depict|portray|narrate|chronicle|trace|"
    r"explore|examine|combine|publish|collect|translate|adapt|call|"
    r"consider|regard|defend|attempt|wish|earn|produce|attribute|"
    r"look|arise|build|create|form|revolve|deal|turn|continue|"
    r"receive|return|marry|visit|sail|fight|grapple|entice|convert|"
    r"preach|develop|compile"
    r")\b",
    re.I,
)
_FILM_SUBJECT = re.compile(
    r"\b(?:"
    r"is an? (?:[\w,'’-]{1,24}\s+){0,10}(?:silent |sound |theatrical |animated |drama )?film\b"
    r"|the film (?:stars|follows|mixes|includes|received|became|was)"
    r"|in the film\b"
    r"|the movie (?:is|was|stars)"
    r"|feature films?(?: and TV specials)?"
    r"|TV specials"
    r"|home video"
    r"|Academy Awards"
    r"|box-office|box office"
    r"|Terminator film"
    r"|Saturday Night Live"
    r"|animated comedy series"
    r"|television programme"
    r"|Paramount Pictures"
    r"|the Muppets"
    r"|\band starring\b"
    r")",
    re.I,
)
_BIO_LEAD = re.compile(
    r"\b([A-Z][\w.'’-]{1,24}(?:\s+[A-Z][\w.'’-]{1,24}){0,5})\s+was an?\s+"
    r"(?:[\w,\"'’-]{1,24}\s+){0,12}"
    r"(writer|novelist|poet|essayist|historian|biographer|diplomat|author|"
    r"playwright|philosopher|statesman|politician|scientist|explorer|"
    r"composer|painter|soldier|general|clergyman|journalist|orator)\b"
)
_LIST_NOTE = re.compile(r"\bthis is a list of\b|\bthis list compiles\b", re.I)
_NON_ENGLISH = re.compile(
    r"\b(fábulas|cuentos|el tercer libro|publicado por primera|conjunto de)\b",
    re.I,
)
_ANACHRONISM = re.compile(
    r"\b(CIA|KGB|Mafia|Lyndon B\.|Schwarzenegger)\b"
)


def _folded(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _title_core(title):
    short = re.sub(r"\s*[—–-]\s*Volume\b.*$", "", title or "", flags=re.I)
    short = re.sub(r",?\s+Vol(?:ume|\.)\s+.*$", "", short, flags=re.I)
    return re.sub(r"^(the|a|an)\s+", "", _folded(short))


def _title_in(text, title):
    core = _title_core(title)
    hay = _folded(text)
    if not core or not hay:
        return False
    if core in hay or hay in core:
        return True
    prefix = " ".join(core.split()[:5])
    if len(prefix) >= 16 and prefix in hay:
        return True
    words = [w for w in core.split() if len(w) > 2]
    if not words:
        return core in hay
    hit = sum(1 for w in words if w in hay.split())
    return hit >= max(1, int(round(len(words) * 0.7)))


def _fold_abbreviations(text):
    text = re.sub(
        r"\b(?:Jr|Sr|St|Mr|Mrs|Ms|Dr|Vol|No|vs|Prof|Rev|Gen|Capt|Lt|Col|etc|e\.g|i\.e|Hon|Jos|Mme|Chas)\.",
        lambda m: m.group(0).replace(".", "@"),
        text,
        flags=re.I,
    )
    text = re.sub(r"\b[A-Z][a-z]{1,2}\.", lambda m: m.group(0).replace(".", "@"), text)
    return re.sub(r"\b[A-Z]\.", lambda m: m.group(0).replace(".", "@"), text)


def wrote_frame(text, title):
    """The whole note is '{Author} wrote {Title}.'"""
    raw = (text or "").strip()
    match = re.fullmatch(r"(.+?)\s+wrote\s+(.+)\.", raw)
    if not match:
        return False
    who, what = match.group(1).strip(), match.group(2).strip()
    if len(who.split()) > 14:
        return False
    if re.search(r"\.\s+[A-Z]", _fold_abbreviations(who)):
        return False
    core = _title_core(title)
    got = re.sub(r"^(the|a|an)\s+", "", _folded(what))
    if not core or not got:
        return False
    got_words = got.split()
    core_words = core.split()
    if len(got_words) > len(core_words) + 3:
        return False
    hit = sum(1 for w in got_words if w in core_words)
    return hit / len(got_words) >= 0.75


def subject_heading_frame(text, title, author=""):
    """The whole note is '{subjects}, in {Author’s Title}.'"""
    raw = (text or "").strip()
    if ", in " not in raw or not raw.endswith("."):
        return False
    parts = raw.split(", in ")
    limit = len(_title_core(title)) + len(author or "") + 60
    for i in range(1, len(parts)):
        head = ", in ".join(parts[:i]).strip()
        tail = ", in ".join(parts[i:]).strip()
        body = tail[:-1].strip()
        break_in_tail = re.search(r"\.\s+[A-Z][a-z]", _fold_abbreviations(body))
        break_in_title = re.search(r"\.\s+[A-Z][a-z]", _fold_abbreviations(title or ""))
        if break_in_tail and not break_in_title:
            continue
        if re.match(r"^In\s+", head) and _title_in(head, title):
            continue
        if re.search(r"\b(is|was|were|are|recounts|describes|follows|tells)\b", head, re.I):
            continue
        if _title_in(body, title) and len(body) <= limit:
            return True
    return False


def _apos(text):
    return (text or "").replace("’", "'").replace("‘", "'").replace("`", "'")


def _short_title(title):
    text = re.sub(r"\s*[—–-]\s*(Complete|Volume\b.*)$", "", title or "", flags=re.I)
    text = re.sub(r",?\s+Vol(?:ume|\.)\s+.*$", "", text, flags=re.I)
    text = text.strip(" ,;—–-")
    if len(text) > 140:
        text = text[:137].rsplit(" ", 1)[0]
    return text or (title or "")[:80]


def _title_candidates(title):
    titles = []
    for candidate in (
        title or "",
        _short_title(title),
        re.split(r"\s*[:;]| -- | — | – ", title or "", maxsplit=1)[0],
    ):
        candidate = candidate.strip()
        if candidate and candidate not in titles:
            titles.append(candidate)
    titles.sort(key=len, reverse=True)
    return titles


def _in_title_rest_exact(text, title):
    """Text after 'In {Title},' when the note is that extract frame. Else None."""
    raw = (text or "").strip()
    if not raw.lower().startswith("in "):
        return None
    hay = _apos(raw)
    for candidate in _title_candidates(title):
        prefix = "In " + _apos(candidate)
        if hay.lower().startswith(prefix.lower()):
            rest = hay[len(prefix):].lstrip()
            if rest.startswith(","):
                return rest[1:].strip()
            return None
    return None


def _norm_colon(text):
    text = _apos(text or "")
    text = re.sub(r"\s*:\s*", ": ", text)
    return re.sub(r"\s+", " ", text).strip()


def _in_title_rest_loose(text, title):
    """Same frame when the title's colon spacing, or a trailing period, differs."""
    raw = _norm_colon(text)
    if not raw.lower().startswith("in "):
        return None
    titles = []
    for candidate in _title_candidates(title):
        candidate = _norm_colon(candidate).strip(" ,;.")
        if candidate and candidate.lower() not in {item.lower() for item in titles}:
            titles.append(candidate)
    titles.sort(key=len, reverse=True)
    for candidate in titles:
        prefix = "In " + candidate
        if not raw.lower().startswith(prefix.lower()):
            continue
        rest = raw[len(prefix):].lstrip()
        rest = re.sub(r"^\.\s*", "", rest)
        if rest.startswith(","):
            return rest[1:].strip()
    return None


def in_title_rest(text, title):
    """Text after 'In {Title},' when the note is that extract frame. Else None.

    A finite verb in the extract does not make this frame a note.
    """
    found = _in_title_rest_exact(text, title)
    if found is not None:
        return found
    return _in_title_rest_loose(text, title)


# Real prose that only needs the 'In {Title},' opener taken off.
STRIP_IN_TITLE_SLUGS = frozenset({
    "rise-and-fall-of-cesar-birotteau",
    "common-sense",
})


def strip_in_title_opener(text, title):
    """Return the body after 'In {Title},' with its first letter capitalized."""
    rest = _in_title_rest_exact(text, title)
    if not rest:
        return None
    rest = rest.strip()
    if not rest:
        return None
    return rest[0].upper() + rest[1:]


# 'published in –', 'written in –71', 'in -', 'in -14'.
# An ASCII hyphen counts only as its own dash, so coming-of-age and son-in-law stay.
PUNCHED_IN_DASH = re.compile(
    r"\bin\s*(?:[–—−]|-)\s*\d{0,4}(?=\s|[,.;:)]|$)",
    re.I,
)
BETWEEN_AND = re.compile(r"\bbetween\s+and\b", re.I)
IN_BY = re.compile(r"\bin\s+by\b", re.I)
BLANK_YEAR_SPAN = re.compile(
    rf"\b\d{{1,2}}\s+(?:{MONTHS})\s*[–—−-]\s*\d{{1,2}}\s+(?:{MONTHS})\b"
    rf"(?!\s*,?\s*(?:1\d{{3}}|20\d{{2}}))",
    re.I,
)


def punched_in_dash(text):
    return bool(PUNCHED_IN_DASH.search(text or ""))


def year_hole_reason(text):
    """A year that was lifted out and left a broken phrase, or None."""
    raw = text or ""
    if BETWEEN_AND.search(raw):
        return "between-and"
    if IN_BY.search(raw):
        return "in-by"
    if BLANK_YEAR_SPAN.search(raw):
        return "blank-year-span"
    if punched_in_dash(raw):
        return "in-dash"
    return None


def repair_year_holes(text):
    """Delete a year hole. Nothing new is written in."""
    s = text or ""
    s = re.sub(
        rf"\(\s*(?:baptised|baptized)\s+\d{{1,2}}\s+(?:{MONTHS})\s*[–—−-]\s*\d{{1,2}}\s+(?:{MONTHS})\s*\)",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"\(\s*\d{{1,2}}\s+(?:{MONTHS})\s*[–—−-]\s*\d{{1,2}}\s+(?:{MONTHS})\s*\)",
        "",
        s,
        flags=re.I,
    )
    s = BLANK_YEAR_SPAN.sub("", s)
    s = re.sub(r"\s+sometime\s+between\s+and\b", "", s, flags=re.I)
    s = re.sub(r"(?:^|(?<=[.!?]\s))Written\s+between\s+and,\s*", "", s)
    s = re.sub(r"\s+between\s+and\s*,", ",", s, flags=re.I)
    s = re.sub(r"\s+between\s+and\b", "", s, flags=re.I)
    s = re.sub(r"\bin\s+by\b", "by", s, flags=re.I)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r",\s*\.", ".", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    return s.strip()


def title_variants(title):
    """Titles as they were pasted into a shared sentence, longest first."""
    title = title or ""
    found = []
    candidates = (
        title,
        _short_title(title),
        re.split(r"\s*[:;]| -- | — | – ", title, maxsplit=1)[0],
        re.sub(r"\s*[—–-]\s*(Complete|Volume\b.*)$", "", title, flags=re.I),
        re.sub(r",?\s+Vol(?:ume|\.)\s+.*$", "", title, flags=re.I),
        re.sub(r",?\s+Part\s+\d+.*$", "", title, flags=re.I),
        re.sub(r",?\s+Chapters\s+.*$", "", title, flags=re.I),
    )
    for candidate in candidates:
        candidate = _apos(candidate).strip(" ,;.-")
        if len(candidate) < 8:
            continue
        if candidate.lower() not in {item.lower() for item in found}:
            found.append(candidate)
    found.sort(key=len, reverse=True)
    return found


def blurb_without_title(text, title):
    """The note with this book's title replaced, so pasted copies compare equal."""
    body = _apos(text or "")
    for variant in title_variants(title):
        body = re.sub(re.escape(variant), " TITLE ", body, flags=re.I)
    return re.sub(r"\s+", " ", body).strip()


def repair_punched_in_dash(text):
    """Delete an 'in –' / 'in –NN' year hole. Nothing new is written in."""
    original = text or ""
    if not punched_in_dash(original):
        return original
    cleaned = PUNCHED_IN_DASH.sub("", original)
    cleaned = re.sub(r",\s*published\s*,\s*", " ", cleaned, flags=re.I)
    cleaned = re.sub(
        r"\b([A-Za-z]{3,})\s+(the year before)\b",
        r"\1, \2",
        cleaned,
    )
    cleaned = re.sub(
        r"(the year before [^–—−]{3,40})\s+[–—−]\s+",
        r"\1, ",
        cleaned,
    )
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r",\s*,+", ",", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    return cleaned.strip()


_SCRAP_TOPIC = re.compile(
    r"Merrie Melodies|Cavalera Conspiracy|\bSepultura\b|Ilene Woods|"
    r"method acting|Primetime Emmy|\bTony Award\b|Golden Globe|"
    r"\bpodcast\b|Sarah Koenig|Jean Shepherd|Masterpiece Theatre|"
    r"Amazing Race|Celebrity Rehab|\bUnsolved Mysteries\b|Tom and Jerry|"
    r"Sofia the First|Once Upon a Studio|Honeymoon Hotel|"
    r"Beaver Mills Lumber|Rat Portage Lumber|\bvoiced by\b",
    re.I,
)


def scrap_topic(text):
    """A film, podcast, award, or other page pasted in place of the book."""
    return bool(_SCRAP_TOPIC.search(text or ""))


def _outside_parens(text):
    outside = re.sub(r"\([^()]*\)", " ", text or "")
    outside = re.sub(r"\([^()]*$", " ", outside)
    return re.sub(r"\s+", " ", outside).strip(" ,;:-")


def cutoff_fragment(text):
    """A title line or gloss that was cut off before it became a sentence."""
    raw = (text or "").strip()
    if not raw:
        return False
    if re.search(r"\blit\.\s+[A-Z]", raw) and raw.count("(") > raw.count(")"):
        return True
    if re.search(r"\b(?:lat|abbr)\.\s+[A-Z]", raw):
        return True
    if raw.count("(") > raw.count(")"):
        outside = _outside_parens(raw)
        if outside and not has_finite_verb(outside) and len(outside) < 140:
            return True
    return False


def trim_dangling_paren(text):
    """Cut a short unclosed parenthesis, or one that is only a leftover sentence."""
    raw = (text or "").strip()
    if raw.count("(") <= raw.count(")"):
        return raw
    start = raw.rfind("(")
    tail = raw[start:]
    if ")" in tail:
        return raw
    head = raw[:start].rstrip()
    if not has_finite_verb(head) or len(head) < 40:
        return raw
    short_tail = len(tail) <= 24
    sentence_tail = head.endswith((".", "!", "?"))
    if not short_tail and not sentence_tail:
        return raw
    if not head.endswith((".", "!", "?")):
        head += "."
    return head


def drop_ripped_name_sentence(text):
    """Remove a final sentence that ends on a punched-out name ('critic J.')."""
    cleaned = re.sub(r"(?:^|\.\s+)[^.]*\bcritic\s+[A-Z]\.\s*$", ".", text or "").strip()
    cleaned = re.sub(
        r"(?:^|\.\s+)[^.]*\bcompanion\s+[A-Z][a-z]+\s+[A-Z]\.\s*$",
        ".",
        cleaned,
    ).strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\.\s*\.", ".", cleaned)
    return cleaned.strip()


def has_finite_verb(text):
    if _AUX.search(text or "") or _FINITE.search(text or ""):
        return True
    for word in re.findall(r"[A-Za-z][A-Za-z'-]{4,}", text or ""):
        low = word.lower()
        # "edited" is 6 letters; "{5,}ed" would require 7 and miss it.
        if re.fullmatch(r"[a-z]{4,}ed", low) and low not in _ED_NOT_FINITE:
            return True
    return False


def verbless_in_title(text, title):
    """'In {Title},' followed by a fragment that never gets a verb."""
    rest = in_title_rest(text, title)
    if rest is None:
        return False
    return not has_finite_verb(rest)


def _month_day(label="day"):
    span = r"\d{1,2}(?:\s*[–—-]\s*\d{1,2})?"
    return rf"(?:{MONTHS})\s+{span}"


def ripped_month_day(text):
    """A month and day left behind after the year was removed."""
    raw = text or ""
    day = _month_day()
    patterns = (
        rf"\(\s*(?:c\.?\s*)?(?:[–—-]\s*)?(?:around\s+)?{day}\s*,\s*\)",
        rf"\bon\s+{day}\s*,(?!\s*(?:1\d{{3}}|20\d{{2}}))(?=\s*(?:in|and|as|at)\b)",
        rf"\bof\s+{day}\s*,(?!\s*(?:1\d{{3}}|20\d{{2}})\b)(?=\s*(?:as|in|and)\b)",
        rf"\b(?:on\s+)?{day}\s+and\s+\d{{1,2}}\s*,\s*\.",
        rf"\bfrom\s+{day}\s+to\s*\.",
        rf"\]\s*[–—-]\s*{day}\s*,\s*\)",
        rf"\baround\s+{day}\s*,\s*\)",
        rf"(?:^|[,(]\s*)[–—-]\s*{day}\s*,\s*\)",
        # "October 7, in New York" — day, comma, preposition, no year.
        rf"\b{day}\s*,\s+in\b(?!\s*(?:1\d{{3}}|20\d{{2}}))",
    )
    return any(re.search(pat, raw, re.I) for pat in patterns)


def repair_ripped_dates(text):
    """Delete a month-day, or a month range, whose year was already removed.

    The words around it stay. Nothing new is written in.
    """
    s = text or ""
    day = _month_day()
    # Strip these before date cleanup, while the parentheses are still closed.
    s = re.sub(r"\s*\((?:[A-Z][a-z]+ )?pronunciation:[^)]*\)", "", s, flags=re.I)
    s = re.sub(r"\s*\(\[[^\]]{1,80}\]\s*\)", "", s)
    s = re.sub(rf"\([^)]{{0,80}}[–—-]\s*{day}\s*,\s*\)", "", s, flags=re.I)
    s = re.sub(rf"\(\s*(?:c\.?\s*)?(?:[–—-]\s*)?(?:around\s+)?{day}\s*,\s*\)", "", s, flags=re.I)
    s = re.sub(rf"\(\s*locally\s*\)", "", s, flags=re.I)
    s = re.sub(rf"\d{{1,2}}\s+(?:{MONTHS})\s*\]\s*[–—-]\s*{day}\s*,\s*\)", "", s, flags=re.I)
    s = re.sub(rf"\]\s*[–—-]\s*{day}\s*,\s*\)", "", s, flags=re.I)
    s = re.sub(rf"(?:^|\s)[–—-]\s*{day}\s*,\s*\)", " ", s, flags=re.I)
    s = re.sub(rf"\baround\s+{day}\s*,\s*\)", "", s, flags=re.I)
    s = re.sub(
        rf"\bon\s+{day}\s*,(?!\s*(?:1\d{{3}}|20\d{{2}}))(?=\s*(?:in|and|as|at)\b)",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(
        rf"\bof\s+{day}\s*,(?!\s*(?:1\d{{3}}|20\d{{2}})\b)(?=\s*(?:as|in|and)\b)",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(rf"\bon\s+{day}\s+and\s+\d{{1,2}}\s*,\s*\.", ".", s, flags=re.I)
    s = re.sub(rf"\b{day}\s+and\s+\d{{1,2}}\s*,\s*\.", ".", s, flags=re.I)
    s = re.sub(rf"\bfrom\s+{day}\s+to\s*\.", ".", s, flags=re.I)
    s = re.sub(rf"\b{day}\s*,\s+in\b(?!\s*(?:1\d{{3}}|20\d{{2}}))", "in", s, flags=re.I)
    # "from March to November" — both years were removed, no day left.
    s = re.sub(
        rf"\bfrom\s+(?:{MONTHS})\s+to\s+(?:{MONTHS})\b",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(published|produced|released|appeared|printed)\s+in\s+by\b",
        r"\1 by",
        s,
        flags=re.I,
    )
    # "In – she held" is a year that was lifted out of the sentence.
    s = re.sub(r"\bIn\s+[–—-]\s+", "", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\(\s*,\s*", "(", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r",\s*,+", ",", s)
    s = re.sub(r"\(\s*,", "(", s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r",\s+\.", ".", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    return s.strip()


_GENERIC_NAME = {
    "christmas", "christian", "american", "english", "french", "german",
    "history", "church", "children", "ancient", "modern", "great", "little",
}


def _person_named(person, title, author=""):
    """True when this person's name is the book or the author, not a stranger."""
    parts = [p for p in _folded(person).split() if len(p) >= 3]
    if not parts:
        return False
    blob = set(_folded(f"{title} {author}").split())
    hits = sum(1 for p in parts if p in blob)
    return hits >= min(2, len(parts)) or (len(parts) == 1 and hits == 1)


def off_topic_reason(text, title, author=""):
    """Why an extract is about the wrong thing, or None when it may stay."""
    raw = text or ""
    if scrap_topic(raw):
        return "scrap"
    if cutoff_fragment(raw):
        return "fragment"
    if _FILM_SUBJECT.search(raw):
        if not re.search(r"\b(film|cinema|movies?)\b", title or "", re.I):
            return "film"
    if _LIST_NOTE.search(raw):
        return "list"
    if _NON_ENGLISH.search(raw):
        return "non-english"
    if _ANACHRONISM.search(raw):
        return "anachronism"
    if re.search(r"\bpronunciation\s*:", raw, re.I):
        return "pronunciation"
    if re.search(r",\s+was born\b|\(\s*or\s+was\b", raw):
        return "missing-subject"
    rest = in_title_rest(raw, title)
    if rest and re.match(r"^(?:was|were|is)\b", rest, re.I):
        return "missing-subject"
    shifted = in_title_rest(raw, title)
    if shifted:
        head = re.sub(r"\([^)]*\)", " ", shifted)
        head = re.sub(r"\s{2,}", " ", head).strip()
        other = re.match(r"^([A-Z][^,]{3,80}), also known as\b", head)
        if other:
            words = [w for w in _folded(other.group(1)).split() if len(w) >= 4]
            title_words = set(_folded(title).split())
            distinctive = [w for w in words if w not in _GENERIC_NAME]
            pool = distinctive or words
            if pool and not any(w in title_words for w in pool):
                return "shifted-subject"
    bio = _BIO_LEAD.search(raw)
    if bio:
        if not _person_named(bio.group(1), title, author):
            return "wrong-person"
        if re.search(r"\b(romance|novel)\b", title or "", re.I) and not re.search(
            r"\b(novel|romance|story|poem|fiction)\b", raw, re.I
        ):
            return "person-not-book"
        if re.search(rf"\bwith\s+{re.escape(bio.group(1))}\b", title or ""):
            return "person-not-book"
    return None


def participle_fragment(text, title):
    """'In {Title}, Name, published by …' with no finite clause."""
    rest = in_title_rest(text, title)
    if not rest or _AUX.search(rest):
        return False
    first = re.split(r"(?<=[.!?])\s+", rest)[0]
    return bool(re.match(
        r"^(?:[A-Z][\w.'’-]{1,24}(?:\s+[A-Z][\w.'’-]{1,24}){0,4}),\s+"
        r"(?:published|illustrated|gathered|released)\b",
        first,
    ))


def broken_extract(text, title, author=""):
    """True when the note is a fragment, a ripped date, or the wrong subject."""
    raw = (text or "").strip()
    if not raw:
        return False
    if (
        in_title_rest(raw, title) is not None
        or year_hole_reason(raw)
        or ripped_month_day(raw)
        or verbless_in_title(raw, title)
        or participle_fragment(raw, title)
        or off_topic_reason(raw, title, author)
    ):
        return True
    return False


def scrub_blurb(text, title, featured=False, author=""):
    """Return (note, action). action is keep, fix, or drop.

    A featured handwritten note is left as stored. A broken extract is repaired
    only by deleting the damaged date; if that still fails, the note is emptied.
    """
    original = (text or "").strip()
    if featured or not original:
        return original, "keep"
    repaired = repair_ripped_dates(original)
    if broken_extract(repaired, title, author):
        return "", "drop"
    if repaired != original:
        if len(repaired) < 40 or not has_finite_verb(repaired):
            return "", "drop"
        return repaired, "fix"
    return original, "keep"


def check_blurb(text, slug, featured=False, title="", author=""):
    text = (text or "").strip()
    if not text:
        if featured:
            raise SystemExit(f"missing featured blurb: {slug}")
        return
    if in_title_rest(text, title) is not None:
        raise SystemExit(f"in-title extract in {slug}")
    hole = year_hole_reason(text)
    if hole:
        raise SystemExit(f"year hole in {slug}: {hole}")
    if verbless_in_title(text, title):
        raise SystemExit(f"verbless extract in {slug}")
    if ripped_month_day(text):
        raise SystemExit(f"month-day with year removed in {slug}")
    reason = off_topic_reason(text, title, author)
    if reason:
        raise SystemExit(f"off-topic extract in {slug}: {reason}")
    if participle_fragment(text, title):
        raise SystemExit(f"verbless extract in {slug}")
    if wrote_frame(text, title):
        raise SystemExit(f"wrote frame in {slug}")
    if subject_heading_frame(text, title, author):
        raise SystemExit(f"subject-heading frame in {slug}")
    if ",," in text:
        raise SystemExit(f"punched-out date in {slug}")
    for phrase in FORBIDDEN_SUBSTRINGS:
        if phrase.lower() in text.lower():
            raise SystemExit(f"retired lead in {slug}: {phrase}")
    if OLD_LEAD.search(text):
        raise SystemExit(f"retired kind-about lead in {slug}")
    ident = text
    if title:
        ident = re.sub(re.escape(title), " ", ident, flags=re.I)
    if CATALOG_ID.search(ident):
        raise SystemExit(f"catalog id or site name in blurb: {slug}")
    # A year that is already part of the book's title is the record, not an invented date.
    scrub = text
    for year in re.findall(r"\b(?:19[3-9]\d|20\d\d)\b", title or ""):
        scrub = scrub.replace(year, "")
    if FUTURE_YEAR.search(scrub):
        raise SystemExit(f"year after 1928 in {slug}")


def _volume_rank(book):
    """Prefer the unsuffixed or lowest-volume copy when blurbs were pasted."""
    slug = book.get("slug") or ""
    volumes = [int(n) for n in re.findall(r"(?:volume|vol|part)[- ]0*(\d+)", slug, flags=re.I)]
    tail = re.search(r"-(\d+)$", slug)
    if volumes:
        vol = volumes[0]
    elif tail and not re.search(r"(?:volume|vol|part)", slug, flags=re.I):
        vol = int(tail.group(1))
    else:
        vol = 0
    try:
        gutenberg = int(book.get("gutenberg") or 10**9)
    except (TypeError, ValueError):
        gutenberg = 10**9
    return (vol, gutenberg, slug)


def check_duplicate_blurbs(catalog):
    """Identical non-featured notes on more than one book fail the build."""
    groups = {}
    slotted = {}
    for book in catalog["books"]:
        text = (book.get("blurb") or "").strip()
        if not text or book.get("featured"):
            continue
        slug = book.get("slug") or "?"
        groups.setdefault(text, []).append(slug)
        key = blurb_without_title(text, book.get("title") or "")
        slotted.setdefault(key, []).append(slug)
    for slugs in groups.values():
        if len(slugs) > 1:
            raise SystemExit(
                f"identical blurb on {len(slugs)} books, including {slugs[0]}"
            )
    for slugs in slotted.values():
        if len(slugs) > 1:
            raise SystemExit(
                f"title-slot blurb on {len(slugs)} books, including {slugs[0]}"
            )


def check_catalog(catalog):
    featured = [b for b in catalog["books"] if b.get("featured")]
    if len(featured) != 45:
        raise SystemExit(f"expected 45 featured books, found {len(featured)}")
    check_duplicate_blurbs(catalog)
    for b in catalog["books"]:
        if b.get("history"):
            raise SystemExit(f"history template still stored on {b.get('slug')}")
        check_blurb(
            b.get("blurb") or "",
            b.get("slug") or "?",
            featured=bool(b.get("featured")),
            title=b.get("title") or "",
            author=b.get("author_name") or "",
        )
    titles_by_author = {}
    for b in catalog["books"]:
        titles_by_author.setdefault(b.get("author"), []).append(b.get("title") or "")
    for author in catalog.get("authors") or []:
        intro = author.get("intro") or ""
        if not intro:
            continue
        scrub = intro
        for year in re.findall(r"\b(?:19[3-9]\d|20\d\d)\b", " ".join(titles_by_author.get(author.get("slug"), []))):
            scrub = scrub.replace(year, "")
        if FUTURE_YEAR.search(scrub):
            raise SystemExit(f"year after 1928 in author note: {author.get('slug')}")
    return len(catalog["books"])


def scrub_catalog(catalog):
    """Empty pasted extracts. Does not write a new template note.

    'In {Title},' extracts are emptied, except Cesar Birotteau and Common Sense,
    which keep the sentence after the opener. Identical copies of one note are
    emptied down to a single volume.
    """
    stats = {
        "in_title_dropped": 0,
        "in_title_rewritten": 0,
        "punchouts_dropped": 0,
        "punchouts_repaired": 0,
        "scraps_dropped": 0,
        "fragments_dropped": 0,
        "dupes_emptied": 0,
    }
    featured_before = {
        b["slug"]: b.get("blurb") for b in catalog["books"] if b.get("featured")
    }
    for book in catalog["books"]:
        if book.get("featured"):
            continue
        original = (book.get("blurb") or "").strip()
        if not original:
            continue
        title = book.get("title") or ""
        slug = book.get("slug") or ""
        had_punch = punched_in_dash(original)
        if in_title_rest(original, title) is not None:
            if slug in STRIP_IN_TITLE_SLUGS:
                rewritten = strip_in_title_opener(original, title)
                if (
                    not rewritten
                    or in_title_rest(rewritten, title) is not None
                    or punched_in_dash(rewritten)
                    or scrap_topic(rewritten)
                ):
                    book["blurb"] = ""
                    stats["in_title_dropped"] += 1
                else:
                    book["blurb"] = rewritten
                    stats["in_title_rewritten"] += 1
            else:
                book["blurb"] = ""
                stats["in_title_dropped"] += 1
            if had_punch:
                stats["punchouts_dropped"] += 1
            continue
        if scrap_topic(original) or cutoff_fragment(original):
            book["blurb"] = ""
            if scrap_topic(original):
                stats["scraps_dropped"] += 1
            else:
                stats["fragments_dropped"] += 1
            continue
        cleaned = trim_dangling_paren(original)
        if punched_in_dash(cleaned):
            cleaned = repair_punched_in_dash(cleaned)
            cleaned = drop_ripped_name_sentence(cleaned)
        if (
            not cleaned
            or scrap_topic(cleaned)
            or cutoff_fragment(cleaned)
            or punched_in_dash(cleaned)
            or (cleaned != original and (len(cleaned) < 40 or not has_finite_verb(cleaned)))
        ):
            book["blurb"] = ""
            if had_punch:
                stats["punchouts_dropped"] += 1
            else:
                stats["fragments_dropped"] += 1
            continue
        if cleaned != original:
            book["blurb"] = cleaned
            if had_punch:
                stats["punchouts_repaired"] += 1
    groups = {}
    for book in catalog["books"]:
        text = (book.get("blurb") or "").strip()
        if not text or book.get("featured"):
            continue
        groups.setdefault(text, []).append(book)
    for copies in groups.values():
        if len(copies) < 2:
            continue
        copies.sort(key=_volume_rank)
        for extra in copies[1:]:
            extra["blurb"] = ""
            stats["dupes_emptied"] += 1
    for book in catalog["books"]:
        if book.get("featured") and book.get("blurb") != featured_before[book["slug"]]:
            raise SystemExit(f"featured blurb changed: {book['slug']}")
    return stats


def scrub_year_holes_and_title_slots(catalog):
    """Delete year holes, then empty pasted copies that differ only by title.

    Does not write a new sentence. One copy of a shared note may stay.
    Featured notes are left as stored.
    """
    stats = {
        "year_repaired": 0,
        "year_dropped": 0,
        "title_slot_groups": 0,
        "title_slots_emptied": 0,
    }
    featured_before = {
        b["slug"]: b.get("blurb") for b in catalog["books"] if b.get("featured")
    }
    for book in catalog["books"]:
        if book.get("featured"):
            continue
        original = (book.get("blurb") or "").strip()
        if not original or not year_hole_reason(original):
            continue
        title = book.get("title") or ""
        cleaned = repair_year_holes(original)
        if punched_in_dash(cleaned):
            cleaned = repair_punched_in_dash(cleaned)
        broken = (
            not cleaned
            or year_hole_reason(cleaned)
            or len(cleaned) < 40
            or not has_finite_verb(cleaned)
            or in_title_rest(cleaned, title) is not None
            or scrap_topic(cleaned)
            or cutoff_fragment(cleaned)
        )
        if broken:
            book["blurb"] = ""
            stats["year_dropped"] += 1
            continue
        book["blurb"] = cleaned
        stats["year_repaired"] += 1
    groups = {}
    for book in catalog["books"]:
        text = (book.get("blurb") or "").strip()
        if not text or book.get("featured"):
            continue
        key = blurb_without_title(text, book.get("title") or "")
        groups.setdefault(key, []).append(book)
    for copies in groups.values():
        if len(copies) < 2:
            continue
        stats["title_slot_groups"] += 1
        copies.sort(key=_volume_rank)
        for extra in copies[1:]:
            extra["blurb"] = ""
            stats["title_slots_emptied"] += 1
    for book in catalog["books"]:
        if book.get("featured") and book.get("blurb") != featured_before[book["slug"]]:
            raise SystemExit(f"featured blurb changed: {book['slug']}")
    return stats
