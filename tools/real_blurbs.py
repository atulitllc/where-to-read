#!/usr/bin/env python3
"""Write one factual sentence per non-featured book.

Sources, in order: a Wikipedia introduction linked from the Gutenberg
bibliographic record, an Open Library work description when it is actually
about the book, then the subject headings on that same bibliographic record.
Years are kept only when they are already on the catalog record (the book's
year, or the author's birth and death) and are not after 1928.

This module stores sentences. It does not assign a lead pattern.
"""
import csv
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog.json"
PG_PATH = Path("/tmp/wtr/pg_catalog.csv")
EXTRACTS_PATH = Path("/tmp/wtr/extracts_by_g.json")
WIKI_TITLES_PATH = Path("/tmp/wtr/wiki_titles.json")
OL_PATH = Path("/tmp/wtr/ol_partial.json")

STOP = {
    "a", "an", "the", "of", "and", "or", "to", "in", "for", "on", "with", "from",
    "by", "at", "as", "into", "over", "its", "his", "her", "their", "vol", "volume",
    "part", "book", "books",
}
FORM_LABEL = (
    ("juvenile fiction", "children"),
    ("juvenile literature", "children"),
    ("children's stories", "children"),
    ("fairy tales", "fairy"),
    ("short stories", "stories"),
    ("personal narratives", "narrative"),
    ("description and travel", "travel"),
    ("social life and customs", "customs"),
    ("autobiography", "autobiography"),
    ("correspondence", "letters"),
    ("biography", "biography"),
    ("fiction", "fiction"),
    ("poetry", "poetry"),
    ("poems", "poetry"),
    ("drama", "drama"),
    ("history", "history"),
    ("sources", "sources"),
    ("essays", "essays"),
    ("sermons", "sermons"),
    ("lectures", "lectures"),
    ("speeches", "speeches"),
    ("diaries", "narrative"),
)
SPAM = (
    "we specialize", "click here", "buy now", "our team", "boat lift",
    "http://", "https://", "**", "add to cart", "free shipping",
)


def tidy(text):
    text = html.unescape(text or "")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(" .", ".").replace(" ;", ";")
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"\(\s*,", "(", text)
    text = re.sub(r"\b(an)\s+([bcdfghjklmnpqrstvwxyz])", r"a \2", text, flags=re.I)
    text = re.sub(r"\b(a)\s+([aeiou])", r"an \2", text, flags=re.I)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,;")
    if text and text[-1] not in ".?!":
        text += "."
    return text


def toks(s):
    return [w for w in re.findall(r"[a-z0-9']+", (s or "").lower()) if w not in STOP and len(w) > 2]


def possessive(name):
    name = (name or "").strip()
    if not name:
        return name
    if name.endswith(("s", "S")):
        return name + "’"
    return name + "’s"


def short_title(title):
    t = re.sub(r"\s*[—–-]\s*(Complete|Volume\b.*)$", "", title or "", flags=re.I)
    t = re.sub(r",?\s+Vol(?:ume|\.)\s+.*$", "", t, flags=re.I)
    t = t.strip(" ,;—–-")
    if len(t) > 140:
        t = t[:137].rsplit(" ", 1)[0]
    return t or (title or "")[:80]


def allowed_years(book):
    years = set()
    for key in ("year", "author_birth", "author_death"):
        val = book.get(key)
        if isinstance(val, int) and 1 <= val <= 1928:
            years.add(val)
    return years


def sentences_of(text):
    raw = re.sub(r"\s+", " ", text or "").strip()
    raw = re.sub(
        r"\b(Dr|Mr|Mrs|Ms|St|Vol|Jr|Sr|Prof|Rev|Gen|Capt|Lt|Col|No|Nos|vs|Mt|cf|ed|eds|trans|ca|approx)\.",
        r"\1@",
        raw,
    )
    raw = re.sub(r"\bc\.(?=\s*\d)", "c@", raw)
    parts = re.findall(r"[^.!?]+[.!?]", raw)
    out = []
    for p in parts:
        p = p.replace("@", ".").strip()
        if p:
            out.append(p)
    return out


def strip_years(sentence, allowed):
    if sentence is None:
        return None
    years = [int(y) for y in re.findall(r"\b(1[0-9]{3}|20[0-9]{2})\b", sentence)]
    if any(y >= 1931 for y in years):
        return None

    def repl(match):
        y = int(match.group(1))
        return match.group(0) if y in allowed else ""

    s = re.sub(r"\b(1[0-9]{3}|20[0-9]{2})\b", repl, sentence)
    s = re.sub(r"\(\s*[-–—,]?\s*\)", "", s)
    s = re.sub(r"\b(in|of|from|around|circa|c\.)\s+(?=[,.)]|$)", "", s)
    s = re.sub(r"\b(in|on|by|during|around)\s+(and|or|but)\b", r"\2", s, flags=re.I)
    s = re.sub(r"\b(in|on|by|around)\s+(during|in|on)\b", "", s, flags=re.I)
    s = re.sub(r"\bc@\s*$", "", s)
    s = re.sub(
        r"\((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*[–-]\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\)",
        "",
        s,
    )
    s = re.sub(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*[–-]\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?",
        "",
        s,
    )
    s = re.sub(r"\s{2,}", " ", s).strip(" ,;")
    if re.search(r"\b(from|between)\s+to\b", s, re.I):
        return None
    if not s or len(s) < 40:
        return None
    return s


def unacceptable(sentence):
    low = sentence.lower()
    if any(w in low for w in (
        "wikipedia", "gutenberg", "open library", "booksthere",
        "this article", "may refer to", "disambiguation",
        "click here", "we specialize",
    )):
        return True
    # Short file-format tokens must be whole words. "epub" sits inside "republic".
    if re.search(r"\b(isbn|pdf|epub|mobi|download)\b", low):
        return True
    if re.search(r"\b(donald trump|covid|internet|website)\b", low):
        return True
    if re.search(r"\bOL\d+W\b", sentence):
        return True
    return False


def paraphrase(sentence, title, anchor=True):
    s = sentence
    swaps = (
        (r"^(?:The|the) novel follows\b", "The story stays with"),
        (r"^(?:The|the) book follows\b", "The story stays with"),
        (r"^(?:The|the) story follows\b", "The story stays with"),
        (r"^It follows\b", "The story stays with"),
        (r"^(?:The|the) novel tells\b", f"{title} tells"),
        (r"^(?:The|the) book tells\b", f"{title} tells"),
        (r"^It tells\b", f"{title} tells"),
        (r"\btells the story of\b", "recounts"),
        (r"\bis the story of\b", "recounts"),
        (r"\bwhich tells of\b", "recounting"),
        (r"\bcent(?:er|re)s on\b", "turns on"),
        (r"\bis about\b", "concerns"),
        (r"\bon the subject of\b", "concerning"),
        (r"\bdeals with\b", "takes up"),
        (r"\bcompiled by\b", "gathered by"),
        (r"\bcollection of\b", "gathering of"),
    )
    for pat, rep in swaps:
        s = re.sub(pat, rep, s)
    if title.lower() not in s.lower():
        anchored = False
        for pat in (
            r"^The narrative\b", r"^The novel\b", r"^The book\b", r"^The story\b",
            r"^The work\b", r"^This novel\b", r"^This book\b", r"^It\b",
        ):
            if re.match(pat, s):
                s = re.sub(pat, title, s, count=1)
                anchored = True
                break
        if not anchored and anchor:
            body = s.rstrip(".")
            first = body.split(" ", 1)[0].lower()
            starter = body.split(" ", 1)[0]
            if (
                first in {"the", "a", "an", "this", "it", "its", "his", "her", "their", "as", "in", "on", "when", "after", "before", "while", "there", "although", "because", "since", "following", "during", "some", "both", "just", "each", "another"}
                or re.match(r"(?i)^(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|several|many|most)\b", body)
                or re.search(r"(?i)ing$", starter)
            ):
                body = body[0].lower() + body[1:]
            body = re.sub(r"^its\b", "the", body)
            if title.lower().startswith("in "):
                s = f"{title}: {body}."
            else:
                s = f"In {title}, {body}."
        elif not anchored:
            s = re.sub(r"^(The novel|The book|The story|This novel|This book|It)\b", title, s, count=1)
    return tidy(s)


def bibliographic_opener(sentence, title):
    """A short 'X is a novel by Y' line, not the sentence that says what happens."""
    if len(sentence) > 280:
        return False
    if re.search(
        r"\bis an? (?:[\w'-]+ ){0,5}(novel|book|play|poem|collection|work|story|romance|treatise|dialogue|essay|memoir|biography|history|compilation|volume)\b",
        sentence,
        re.I,
    ):
        return True
    head = sentence
    if title and sentence.lower().startswith(title.lower()):
        head = sentence[len(title):]
    return bool(re.match(r"^\s*,?\s*(is|was)\s+(an?|the)\b", head, re.I))


def author_for_blurb(name):
    name = re.sub(r",?\s*-\d{3,4}\b", "", name or "")
    return re.sub(r"\s+", " ", name).strip(" ,")


def source_fits(text, book):
    """Reject a concept article that only shares one word with the title."""
    low = re.sub(r"\s+", " ", text or "").lower()
    author_bits = [w for w in toks(author_for_blurb(book.get("author_name"))) if len(w) >= 4]
    if any(w in low for w in author_bits):
        return True
    title_bits = [w for w in toks(short_title(book.get("title") or "")) if len(w) >= 5]
    hits = [w for w in title_bits if w in low]
    if len(hits) >= 2:
        return True
    if len(text) < 240 and re.search(r"\b(tale|tales|novel|poem|poems|play|story|stories|essay|essays|letters)\b", low):
        return True
    return False


def from_prose(text, book):
    if not text or len(text) < 50:
        return None
    if not source_fits(text, book):
        return None
    allowed = allowed_years(book)
    title = book.get("title") or ""
    cleaned = re.sub(r"\[[0-9]+\]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    parts = []
    for sentence in sentences_of(cleaned):
        sentence = strip_years(sentence, allowed)
        if not sentence or unacceptable(sentence):
            continue
        parts.append(sentence)
    if not parts:
        return None
    specific = [s for s in parts if not bibliographic_opener(s, title)]
    chosen = (specific or parts)[:2]
    if len(chosen) == 2 and len(chosen[0]) > 220:
        chosen = chosen[:1]
    out = " ".join(paraphrase(s, short_title(title), anchor=(i == 0)) for i, s in enumerate(chosen))
    out = tidy(out)
    if len(out) > 520:
        # keep the first sentence only if the pair ran long
        out = tidy(paraphrase(chosen[0], short_title(title)))
    if len(out) < 60 or len(out) > 700:
        return None
    if unacceptable(out):
        return None
    if not title_in_text(out, title):
        return None
    return out


def folded(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


# Words that show up in both a book title and an unrelated article.
TOPIC_WORDS = {
    "history", "story", "stories", "complete", "works", "letters", "poems", "poetry",
    "essays", "novel", "novels", "romance", "republic", "adventures", "adventure",
    "life", "lives", "tale", "tales", "book", "books", "volume", "part", "other",
    "sketches", "papers", "articles", "collected", "william", "american", "english",
    "french", "german", "italian", "spanish", "ancient", "modern", "great", "little",
    "young", "world", "religion", "science", "philosophy", "politics", "political",
    "america", "england", "france", "germany", "italy", "europe", "africa", "asia",
    "london", "paris", "rome", "ethics", "poems", "plays", "play", "short",
    "fiction", "classic", "classics",
}


def article_matches(book_title, wiki_title, author=""):
    """The Wikipedia page has to be this book, not a word that also appears in the title."""
    if not wiki_title or not book_title:
        return False
    wiki = folded(re.sub(r"\([^)]*\)", " ", wiki_title))
    book = folded(book_title)
    main = folded(re.split(r"\s*[:;]| -- | — | – ", book_title, maxsplit=1)[0])
    if not wiki or not main:
        return False
    if wiki == main or wiki == book:
        return True
    if len(wiki.split()) >= 2 and wiki in book:
        return True
    if len(main.split()) >= 2 and main in wiki:
        return True
    author_toks = set(folded(author).split())
    wiki_toks = [t for t in wiki.split() if len(t) >= 4]
    book_toks = set(book.split())
    shared = [
        t for t in wiki_toks
        if t in book_toks and t not in TOPIC_WORDS and t not in author_toks and t not in STOP
    ]
    if any(t in {"league", "statue", "bibliography", "discography", "filmography", "monument"} for t in wiki.split()):
        return False
    if len(shared) >= 2:
        return True
    if len(shared) == 1 and len(shared[0]) >= 6:
        return True
    content = [t for t in wiki.split() if len(t) >= 4 and t not in STOP]
    if len(content) >= 2 and all(t in book_toks for t in content):
        return True
    return False


def title_in_text(text, title):
    """True when the catalog title is in the sentence, ignoring colon spacing."""
    for candidate in (short_title(title), title or ""):
        needle = folded(candidate)
        if needle and needle in folded(text):
            return True
    return False


COMMON = {
    "revenge", "bankruptcy", "business", "enterprises", "love", "stories", "story",
    "young", "women", "sisters", "courtship", "death", "adventure", "adventurers",
    "orphans", "conduct", "life", "aunts", "cheerfulness", "crime", "voyages",
    "travels", "seafaring", "rescues", "shipwrecks", "married", "people", "daily",
    "history", "revolution", "fairy", "tales", "verse", "play", "letters", "essays",
    "middle", "class", "cosmetics", "industry", "abolitionists", "movements",
    "literature", "fiction", "travel", "war", "murder", "mystery", "poetry", "poems",
    "children", "child", "boys", "girls", "animals", "nature", "science", "religion",
    "philosophy", "politics", "government", "social", "classes", "domestic", "short",
    "personal", "account", "documents", "sources", "sermons", "lectures", "speeches",
    "biography", "autobiography", "correspondence", "description", "customs",
    "juvenile", "humor", "humour", "satire", "ethics", "moral", "education",
    "schools", "teachers", "medicine", "health", "disease", "plants", "birds",
    "insects", "geology", "astronomy", "mathematics", "chemistry", "physics",
    "law", "trials", "prisons", "slavery", "labour", "labor", "industry",
    "railroads", "ships", "sea", "ocean", "islands", "mountains", "rivers",
    "kings", "queens", "princes", "princesses", "knights", "soldiers", "army",
    "navy", "battles", "campaigns", "revolution", "rebellion", "independence",
    "church", "bible", "christian", "clergy", "missions", "prayer", "soul",
    "love", "marriage", "family", "parents", "fathers", "mothers", "widows",
    "ghosts", "supernatural", "magic", "witches", "fairies", "goblins", "dragons",
    "pirates", "treasure", "islands", "voyages", "explorers", "indians", "tribes",
    "settlers", "pioneers", "farm", "farms", "agriculture", "gardening", "flowers",
    "music", "art", "painting", "architecture", "theatre", "theater", "actors",
    "authors", "poets", "writers", "journalists", "newspapers", "periodicals",
    "essays", "sketches", "anecdotes", "letters", "diaries", "memoirs",
    "conduct", "etiquette", "household", "cooking", "recipes", "games", "sports",
    "hunting", "fishing", "dogs", "horses", "cats", "birds", "natural",
    "selection", "evolution", "species", "botany", "zoology", "anatomy",
    "surgery", "nursing", "hygiene", "diet", "temperance", "alcohol",
    "poverty", "charity", "labor", "wages", "strikes", "socialism", "democracy",
    "republic", "constitution", "congress", "parliament", "elections", "suffrage",
    "women", "rights", "property", "inheritance", "wills", "contracts",
    "revenge", "jealousy", "ambition", "honor", "honour", "duty", "faith",
    "friendship", "courage", "cowardice", "guilt", "innocence", "justice",
    "detectives", "police", "criminals", "prisoners", "escape", "disguise",
    "shipwrecks", "storms", "lighthouses", "sailors", "captains", "mutiny",
    "colonies", "empire", "colonial", "missionaries", "traders", "merchants",
    "bankers", "speculation", "credit", "money", "gold", "mines", "miners",
    "factories", "mills", "cotton", "wool", "silk", "textiles", "inventors",
    "inventions", "electricity", "telegraph", "telephone", "railways", "steam",
    "engines", "machines", "tools", "building", "houses", "furniture",
    "costume", "dress", "fashion", "beauty", "cosmetics", "perfumes",
    "food", "bread", "wine", "beer", "coffee", "tea", "cookery",
    "schools", "colleges", "universities", "students", "teachers", "readers",
    "language", "grammar", "dictionaries", "translation", "translations",
    "criticism", "reviews", "biography", "biographies", "genealogies",
    "legends", "myths", "mythology", "folklore", "ballads", "songs", "hymns",
    "sermons", "prayers", "meditations", "maxims", "proverbs", "fables",
    "allegories", "romances", "novels", "tales", "sketches", "dialogues",
    "orations", "addresses", "speeches", "debates", "essays", "tracts",
    "pamphlets", "catalogs", "catalogues", "bibliographies", "indexes",
    "maps", "atlases", "guidebooks", "tours", "journeys", "travels",
    "residence", "description", "manners", "customs", "society", "court",
    "courtiers", "nobility", "peasantry", "working", "classes", "poor",
    "rich", "wealth", "luxury", "poverty", "charities", "hospitals",
    "asylums", "prisons", "reform", "punishment", "crime", "criminals",
    "trials", "judges", "lawyers", "juries", "evidence", "witnesses",
    "duels", "honour", "reputation", "scandal", "gossip", "satire",
    "comedy", "tragedy", "farce", "melodrama", "opera", "ballet",
    "painting", "sculpture", "engraving", "photography", "illustration",
    "children", "youth", "boys", "girls", "schools", "orphans", "widows",
    "widowers", "bachelors", "spinsters", "courtship", "engagement",
    "weddings", "divorce", "adultery", "seduction", "inheritance",
    "lost", "found", "identity", "mistaken", "twins", "brothers",
    "sisters", "cousins", "uncles", "aunts", "grandparents", "servants",
    "masters", "slaves", "slavery", "emancipation", "abolition",
    "plantations", "cotton", "tobacco", "sugar", "rice", "wheat",
    "famine", "plague", "cholera", "fever", "wounds", "physicians",
    "surgeons", "nurses", "remedies", "herbs", "poisons", "drugs",
    "astronomy", "stars", "planets", "comets", "moon", "sun", "earth",
    "geology", "rocks", "fossils", "volcanoes", "earthquakes", "climate",
    "weather", "storms", "winds", "rains", "floods", "drought",
    "forests", "trees", "woods", "gardens", "flowers", "fruits",
    "birds", "beasts", "fishes", "insects", "reptiles", "whales",
    "dogs", "horses", "cattle", "sheep", "hunting", "shooting", "fishing",
    "games", "chess", "cards", "sports", "racing", "cricket", "football",
    "boats", "ships", "sailing", "navigation", "harbors", "harbours",
    "ports", "docks", "lighthouses", "wrecks", "pirates", "smugglers",
    "soldiers", "officers", "generals", "battles", "sieges", "camps",
    "strategy", "tactics", "weapons", "artillery", "cavalry", "infantry",
    "navy", "admirals", "sailors", "marines", "privateers", "mutiny",
    "kings", "queens", "princes", "princesses", "emperors", "empresses",
    "courts", "palaces", "castles", "abbeys", "cathedrals", "churches",
    "monasteries", "convents", "monks", "nuns", "priests", "bishops",
    "popes", "saints", "martyrs", "miracles", "relics", "pilgrims",
    "crusades", "heresy", "inquisition", "reformation", "puritans",
    "quakers", "methodists", "catholics", "protestants", "jews", "muslims",
    "philosophy", "logic", "metaphysics", "ethics", "morals", "virtue",
    "vice", "happiness", "death", "immortality", "soul", "god", "gods",
    "mythology", "legends", "heroes", "giants", "fairies", "ghosts",
    "witches", "magic", "alchemy", "astrology", "dreams", "visions",
    "madness", "melancholy", "passion", "jealousy", "revenge", "ambition",
    "pride", "vanity", "greed", "charity", "mercy", "justice", "liberty",
    "equality", "rights", "duty", "patriotism", "exile", "prison",
    "escape", "disguise", "secrets", "letters", "diaries", "confessions",
}
PLACES = {
    "paris", "london", "england", "france", "rome", "italy", "spain", "india",
    "africa", "asia", "europe", "america", "australia", "canada", "germany",
    "ireland", "scotland", "wales", "russia", "china", "japan", "egypt",
    "greece", "boston", "york", "venice", "cuba", "mexico", "switzerland",
    "belgium", "holland", "netherlands", "norway", "sweden", "denmark",
    "portugal", "austria", "hungary", "poland", "turkey", "persia", "arabia",
    "palestine", "jerusalem", "athens", "florence", "naples", "milan", "vienna",
    "berlin", "oxford", "cambridge", "edinburgh", "dublin", "brittany",
    "normandy", "provence", "sicily", "corsica", "alaska", "hawaii", "texas",
    "virginia", "california", "ohio", "kentucky", "pennsylvania", "labrador",
    "newfoundland", "borneo", "java", "sumatra", "ceylon", "burma", "siam",
    "brazil", "peru", "chile", "argentina", "morocco", "algeria", "tunisia",
    "syria", "damascus", "constantinople", "petersburg", "moscow", "warsaw",
    "prague", "geneva", "zurich", "lisbon", "madrid", "seville", "barcelona",
}


def soften(part):
    words = []
    for word in (part or "").split():
        bare = re.sub(r"[^A-Za-z'-]", "", word)
        low = bare.lower()
        if low in PLACES:
            words.append(bare[:1].upper() + bare[1:].lower())
            continue
        if low in COMMON:
            if words and words[-1][:1].isupper() and low in {
                "mountains", "islands", "river", "bay", "hill", "hills", "lake",
                "county", "street", "city", "island",
            }:
                words.append(word[:1].upper() + word[1:])
            else:
                words.append(word[:1].lower() + word[1:])
            continue
        words.append(word)
    return " ".join(words)


def clean_topic(part):
    part = re.sub(r"\s+", " ", part or "").strip(" ,;")
    part = re.sub(r"\s*\([^)]*\)", "", part).strip()
    part = re.sub(r",?\s+\d{3,4}\??\s*[-–]\s*\d{0,4}\??", "", part)
    part = re.sub(r",?\s+\d{3,4}\s*(BCE|BC|B\.C\.?).*$", "", part, flags=re.I)
    part = re.sub(r",?\s+\d{1,3}(st|nd|rd|th)\s+century.*$", "", part, flags=re.I)
    part = part.strip(" ,;-")
    if re.fullmatch(r"\d{3,4}.*", part):
        return ""
    name = False
    if re.match(r"^[A-Z][^,]{1,40}, [A-Z]", part) and not re.search(r"\b(War|History|Fiction)\b", part):
        last, rest = part.split(",", 1)
        part = (rest.strip() + " " + last.strip()).strip()
        name = True
    part = re.sub(r"\s+", " ", part).strip(" ,;")
    if not part or len(part) > 80:
        return ""
    if name:
        return part
    return soften(part)


def classify(part):
    low = re.sub(r"\s+", " ", (part or "").strip().lower())
    low = re.sub(r",?\s+\d{3,4}.*$", "", low).strip()
    for key, label in FORM_LABEL:
        if low == key or low.endswith(" " + key):
            return label
    if low.startswith("early works"):
        return "skip"
    if "translations into english" in low:
        return "skip"
    return None


def heading_bits(heading):
    """Return a noun phrase and a form label. The phrase is the heading's own topic."""
    parts = [p.strip() for p in heading.split("--") if p.strip()]
    forms = []
    topics = []
    for part in parts:
        kind = classify(part)
        if kind == "skip":
            continue
        if re.fullmatch(r"\d{1,3}(st|nd|rd|th) century", part.strip().lower()):
            continue
        if kind:
            forms.append(kind)
            continue
        topic = clean_topic(part)
        if topic:
            topics.append(topic)
    seen = set()
    topics = [t for t in topics if not (t.lower() in seen or seen.add(t.lower()))]
    form = forms[0] if forms else ""
    if "customs" in forms and topics:
        phrase = "daily life in " + " and ".join(topics)
    elif "travel" in forms and topics:
        phrase = "travel in " + " and ".join(topics)
    elif "history" in forms and topics:
        phrase = "the history of " + " and ".join(topics)
    elif "biography" in forms and topics:
        phrase = "the life of " + " and ".join(topics)
    elif len(topics) >= 2:
        phrase = topics[0] + " in " + " and ".join(topics[1:])
    elif topics:
        phrase = topics[0]
    elif form == "fairy":
        phrase = "fairy tales"
    elif form == "poetry":
        phrase = "verse"
    elif form == "drama":
        phrase = "a play"
    elif form == "letters":
        phrase = "letters"
    elif form == "stories":
        phrase = "short stories"
    elif form in {"essays", "sermons", "lectures", "speeches"}:
        phrase = form
    else:
        phrase = ""
    if phrase.lower().startswith("united states") or phrase.lower().startswith("united kingdom"):
        phrase = "the " + phrase
    return phrase, form


def english_join(items):
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def title_already_says(phrase, title):
    pt = set(toks(phrase))
    tt = set(toks(title))
    if not pt:
        return True
    return len(pt & tt) / len(pt) >= 0.7


def from_subjects(book, subject_string):
    title = short_title(book.get("title") or "")
    author = author_for_blurb(book.get("author_name"))
    who = possessive(author) if author else ""
    headings = [h.strip() for h in (subject_string or "").split(";") if h.strip()]
    phrases = []
    forms = []
    for heading in headings:
        phrase, form = heading_bits(heading)
        if form:
            forms.append(form)
        if phrase and not title_already_says(phrase, title):
            phrases.append(phrase)
    specific = [p for p in phrases if p not in {"verse", "a play", "letters", "short stories", "fairy tales", "essays", "sermons"}]
    use = specific or phrases
    seen = set()
    use = [p for p in use if not (p.lower() in seen or seen.add(p.lower()))][:4]
    core = english_join(use)
    if core:
        core_cap = core[:1].upper() + core[1:]
        shown = re.sub(r"^(The|A|An)\s+", "", title) if who else title
        head = f"{who} {shown}" if who and len(shown) < 110 else title
        return tidy(f"{core_cap}, in {head}.")
    # Headings repeat the title, or they name only a form. Say who wrote it.
    if author:
        return tidy(f"{author} wrote {title}.")
    return tidy(f"{title} is the text on this record.")


def ol_description(rec, book):
    if not isinstance(rec, dict):
        return ""
    desc = rec.get("desc") or ""
    if isinstance(desc, dict):
        desc = desc.get("value") or ""
    desc = re.sub(r"<[^>]+>", " ", desc or "")
    desc = re.sub(r"\s+", " ", desc).strip()
    low = desc.lower()
    if len(desc) < 50 or any(s in low for s in SPAM):
        return ""
    words = set(toks(book.get("title"))) | set(toks(book.get("author_name")))
    if len(words & set(toks(desc))) < 1:
        return ""
    return desc


def load_pg():
    rows = {}
    if not PG_PATH.exists():
        return rows
    with PG_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                rows[int(row["Text#"])] = row.get("Subjects") or ""
            except (KeyError, ValueError):
                pass
    return rows


def gatsby_fix(text):
    if "2021" not in text:
        return text
    head = text.split(". Fitzgerald", 1)[0].strip()
    if not head.endswith("."):
        head += "."
    return head


def acceptable_blurb(text, book):
    from blurb_gate import check_blurb
    try:
        check_blurb(
            text,
            book.get("slug") or "?",
            featured=bool(book.get("featured")),
            title=book.get("title") or "",
        )
    except SystemExit:
        return False
    return True


def compose_one(book, pg_subjects, extract, ol_rec, wiki_title=""):
    if book.get("featured"):
        text = book.get("blurb") or ""
        if book.get("slug") == "the-great-gatsby":
            text = gatsby_fix(text)
        return text, "featured"
    prose = None
    if extract and article_matches(book.get("title") or "", wiki_title, book.get("author_name") or ""):
        prose = from_prose(extract, book)
    if prose and acceptable_blurb(prose, book):
        return prose, "wiki"
    ol_text = from_prose(ol_description(ol_rec, book), book) if ol_rec else None
    if ol_text and acceptable_blurb(ol_text, book):
        return ol_text, "ol"
    text = from_subjects(book, pg_subjects)
    if not acceptable_blurb(text, book):
        author = author_for_blurb(book.get("author_name"))
        title = short_title(book.get("title") or "")
        text = tidy(f"{author} wrote {title}.") if author else tidy(f"{title}.")
    return text, "subjects"


def apply_to_catalog(catalog, extracts, ol, pg, wiki_titles=None):
    counts = {"featured": 0, "wiki": 0, "ol": 0, "subjects": 0}
    wiki_titles = wiki_titles or {}
    for book in catalog["books"]:
        book.pop("history", None)
        g = str(book.get("gutenberg"))
        text, kind = compose_one(
            book,
            pg.get(int(book["gutenberg"]), ""),
            extracts.get(g) or "",
            ol.get(book.get("ol_id")) or {},
            wiki_titles.get(g) or "",
        )
        book["blurb"] = text
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def main():
    if not EXTRACTS_PATH.exists() or not PG_PATH.exists():
        raise SystemExit(
            "Refusing to rewrite blurbs without the Wikipedia extracts and the Gutenberg subject file."
        )
    catalog = json.loads(CATALOG_PATH.read_text())
    extracts = json.loads(EXTRACTS_PATH.read_text())
    wiki_titles = json.loads(WIKI_TITLES_PATH.read_text()) if WIKI_TITLES_PATH.exists() else {}
    ol = json.loads(OL_PATH.read_text()) if OL_PATH.exists() else {}
    pg = load_pg()
    counts = apply_to_catalog(catalog, extracts, ol, pg, wiki_titles)
    from blurb_gate import check_catalog
    n = check_catalog(catalog)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print("wrote", n, counts)


if __name__ == "__main__":
    main()
