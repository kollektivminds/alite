# alite_backend/api/trainer/translit.py
import re

# Digraphs must be replaced first to prevent partial character collisions
DIGRAPH_MAP = [
    ("shch", "щ"),
    ("yo", "ё"),
    ("zh", "ж"),
    ("kh", "х"),
    ("ts", "ц"),
    ("ch", "ч"),
    ("sh", "ш"),
    ("yu", "ю"),
    ("ya", "я"),
    ("ye", "е"),
    ("šč", "щ"),
]

SINGLE_MAP = {
    "a": "а",
    "b": "б",
    "v": "в",
    "w": "в",
    "g": "г",
    "d": "д",
    "e": "е",
    "z": "з",
    "i": "и",
    "j": "й",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "f": "ф",
    "h": "х",
    "c": "ц",
    "y": "ы",
    "'": "ь",
    "`": "ъ",
    '"': "ъ",
    "č": "ч",
    "š": "ш",
    "ž": "ж",
}


def is_latin_text(text: str) -> bool:
    """Checks if the query string contains any Latin characters."""
    return bool(re.search(r"[a-zA-Z]", text))


def latin_to_cyrillic(text: str) -> str:
    """Deterministically converts Latin romanization into plain Cyrillic."""
    res = text.strip().lower()
    for lat, cyr in DIGRAPH_MAP:
        res = res.replace(lat, cyr)
    return "".join(SINGLE_MAP.get(ch, ch) for ch in res)
