"""
add_transliteration.py
Adds English phonetic transliterations to every voter record in voters.json.
Fields added:
  - voter_name_en     : searchable English transliteration of voter name
  - relation_name_en  : searchable English transliteration of relation name

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


def telugu_to_searchable(text: str) -> str:
    """
    Transliterate Telugu text to a combined ASCII-only searchable string.
    Multiple phonetic schemes are tried and merged so that common English
    spellings (Ramesh, Sudhir, Jagadish …) all match.
    """
    if not text:
        return ""

    text = text.strip()
    if not text:
        return ""

    variants: set[str] = set()

    for scheme in (sanscript.IAST, sanscript.ITRANS, sanscript.HK):
        try:
            r = transliterate(text, sanscript.TELUGU, scheme)
            r = strip_diacritics(r).lower()
            # keep only ASCII letters, digits, spaces
            r = re.sub(r"[^a-z0-9\s]", "", r)
            r = re.sub(r"\s+", " ", r).strip()
            if r:
                variants.add(r)
        except Exception:
            pass

    return " ".join(sorted(variants))


def main():
    input_file = "voters.json"
    output_file = "voters.json"

    print(f"Loading {input_file} …")
    with open(input_file, encoding="utf-8") as f:
        voters = json.load(f)

    print(f"Transliterating {len(voters)} voter records …")
    for i, v in enumerate(voters):
        v["voter_name_en"]    = telugu_to_searchable(v.get("voter_name", ""))
        v["relation_name_en"] = telugu_to_searchable(v.get("relation_name", ""))
        if (i + 1) % 500 == 0:
            print(f"  … {i + 1} / {len(voters)} done")

    print(f"Writing {output_file} …")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(voters, f, ensure_ascii=False, indent=2)

    print("Done! Sample output:")
    for v in voters[:5]:
        print(f"  {v['voter_name']} -> {v['voter_name_en']}")


if __name__ == "__main__":
    main()
