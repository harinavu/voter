"""
add_transliteration.py
Adds English phonetic transliterations to every voter record in voters.json.

Fields added / updated:
  - voter_name_en        : searchable string (all scheme variants merged)
  - relation_name_en     : searchable string (all scheme variants merged)
  - voter_name_display   : clean display-ready English name (title case, ITRANS)
  - relation_name_display: clean display-ready English relation name

Run:  python3 add_transliteration.py
"""

import json
import unicodedata
import re

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def strip_diacritics(text: str) -> str:
    """Remove combining diacritic marks so ā→a, ī→i, ṭ→t, etc."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if not unicodedata.combining(c))


def clean_ascii(text: str) -> str:
    """Strip diacritics, lowercase, remove non-ASCII-letter/digit/space chars."""
    text = strip_diacritics(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def telugu_to_searchable(text: str) -> str:
    """
    Transliterate Telugu text to a combined ASCII-only searchable string.
    Multiple phonetic schemes are tried and merged so that common English
    spellings (Ramesh, Sudhir, Jagadish …) all match.
    """
    if not text or not text.strip():
        return ""

    variants: set[str] = set()

    for scheme in (sanscript.IAST, sanscript.ITRANS, sanscript.HK):
        try:
            r = transliterate(text.strip(), sanscript.TELUGU, scheme)
            r = clean_ascii(r)
            if r:
                variants.add(r)
        except Exception:
            pass

    return " ".join(sorted(variants))


def telugu_to_display(text: str) -> str:
    """
    Return a single clean, title-cased English transliteration for display.
    Uses ITRANS which gives the most natural-looking English spellings.
    Falls back to IAST if ITRANS fails.
    """
    if not text or not text.strip():
        return ""

    text = text.strip()

    for scheme in (sanscript.ITRANS, sanscript.IAST):
        try:
            r = transliterate(text, sanscript.TELUGU, scheme)
            r = clean_ascii(r)
            if r:
                # Title-case each word
                return " ".join(w.capitalize() for w in r.split())
        except Exception:
            pass

    return ""


def main():
    input_file = "voters.json"
    output_file = "voters.json"

    print(f"Loading {input_file} …")
    with open(input_file, encoding="utf-8") as f:
        voters = json.load(f)

    print(f"Transliterating {len(voters)} voter records …")
    for i, v in enumerate(voters):
        name     = v.get("voter_name", "")
        rel_name = v.get("relation_name", "")

        v["voter_name_en"]         = telugu_to_searchable(name)
        v["relation_name_en"]      = telugu_to_searchable(rel_name)
        v["voter_name_display"]    = telugu_to_display(name)
        v["relation_name_display"] = telugu_to_display(rel_name)

        if (i + 1) % 500 == 0:
            print(f"  … {i + 1} / {len(voters)} done")

    print(f"Writing {output_file} …")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(voters, f, ensure_ascii=False, indent=2)

    print("\nDone! Sample output:")
    for v in voters[:8]:
        print(f"  Telugu:  {v['voter_name']}")
        print(f"  Display: {v['voter_name_display']}")
        print(f"  Search:  {v['voter_name_en']}")
        print()


if __name__ == "__main__":
    main()
