"""
add_transliteration.py
Reads voters_raw.json, applies a linguistically-correct Telugu→English
transliteration, and writes the final voters.json.

Fields added:
  voter_name_display    — clean title-case English name for display
  relation_name_display — clean title-case English relation name
  voter_name_en         — multi-variant searchable string
  relation_name_en      — multi-variant searchable string

Run:  python3 add_transliteration.py
"""

import json
import re
import unicodedata

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Telugu source cleaning  (run BEFORE transliteration)
# ─────────────────────────────────────────────────────────────────────────────

# Telugu vowel matras that the PDF scanner often duplicates by mistake
_DUP_MATRAS = 'ాిీుూెేైొోౌ'

# Stop phrases that bleed into voter_name due to PDF cell extraction bugs
_JUNK_LABELS = [
    'తల్లి పేరు', 'తండ్రి పేరు', 'తండ్రిి పేరు',
    'భర్త పేరు', 'భర్తు పేరు', 'భర్తిి పేరు',
    'వయస్సు', 'వయసు', 'లింగము', 'ఇంటి సంఖ్య',
]


def clean_telugu_source(text: str) -> str:
    """Remove PDF extraction artefacts from Telugu text before transliteration."""
    if not text:
        return ""

    # 1. Strip anything after a junk label (тал్లి పేరు etc.)
    for label in _JUNK_LABELS:
        idx = text.find(label)
        if idx != -1:
            text = text[:idx]

    # 2. Remove embedded newlines (PDF column bleed artefacts)
    text = text.replace('\n', ' ').replace('\r', ' ')

    # 3. Remove trailing/isolated ASCII letters that are PDF column artefacts
    #    e.g. "కే పవీణ్ A" → "కే పవీణ్"
    text = re.sub(r'\s+[A-Z]\s*$', '', text)

    # 4. Collapse consecutive duplicate vowel matras:  ీీ → ీ,  ాా → ా, ంం → ం
    for c in _DUP_MATRAS + 'ంంఃఁ':
        text = re.sub(re.escape(c) + r'{2,}', c, text)

    # 5. Collapse runs of spaces
    text = re.sub(r' {2,}', ' ', text).strip()
    return text


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — ITRANS transliteration + ASCII normalisation
# ─────────────────────────────────────────────────────────────────────────────

def _strip_diacritics(text: str) -> str:
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if not unicodedata.combining(c))


def _to_ascii(text: str) -> str:
    """ITRANS → strip diacritics → lowercase → keep only a-z 0-9 space."""
    text = _strip_diacritics(text).lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = re.sub(r' {2,}', ' ', text).strip()
    return text


def _transliterate_scheme(text: str, scheme) -> str:
    try:
        return transliterate(text, sanscript.TELUGU, scheme)
    except Exception:
        return ''


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Post-processing: Telugu phonological corrections
# ─────────────────────────────────────────────────────────────────────────────

def _fix_phonology(text: str) -> str:
    """
    Apply Telugu-specific phonological rules to the ASCII output of ITRANS.

    Rules applied (in order):
      1. Collapse PDF-artefact doubled vowels: aa→a, ii→i, uu→u, ee→e
      2. rikara (kRRi / rRRi) → kri / ri  (కృ → Kri, not Krri)
      3. mm at word-end → m  (DoubleAanusvara artefact: Gaddamm → Gaddam)
      4. Anusvara nasalisation: 'm' before non-labial consonants → 'n'
            Vemkata → Venkata, Pamdilla → Pandilla, Gumta → Gunta
            Labials (p, b, m) retain 'm': Kampda stays Kampda
    """

    # 1. Collapse doubled long-vowel artefacts
    text = re.sub(r'a{2,}', 'a', text)
    text = re.sub(r'i{2,}', 'i', text)
    text = re.sub(r'u{2,}', 'u', text)
    text = re.sub(r'e{2,}', 'e', text)
    text = re.sub(r'o{2,}', 'o', text)

    # 2. rikara: krri → kri,  rrri → ri  (generalised)
    text = re.sub(r'([a-z])rri', r'\1ri', text)   # e.g. krri → kri
    text = re.sub(r'^rri', 'ri', text)

    # 3. Double-m at word boundary → single m
    text = re.sub(r'mm\b', 'm', text)

    # 4. Anusvara context-sensitive nasalisation
    #    'm' (from ITRANS anusvara M) before a consonant that is NOT a labial
    #    → becomes 'n'.
    #    Non-labials that follow: k, g, c, j, t, d, n, l, r, s, v, y, h, z, q
    #    Labials: p, b, m  — keep 'm' before these
    text = re.sub(
        r'm([kgcjtdnlrsvyhzqwx])',
        r'n\1',
        text
    )

    return text


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def telugu_to_display(raw_telugu: str) -> str:
    """
    Return a single clean, title-cased English transliteration for display.
    Uses ITRANS (most natural-looking spellings) with full post-processing.
    """
    text = clean_telugu_source(raw_telugu)
    if not text:
        return ''

    itrans = _transliterate_scheme(text, sanscript.ITRANS)
    if not itrans:
        return ''

    ascii_text = _to_ascii(itrans)
    ascii_text = _fix_phonology(ascii_text)

    if not ascii_text:
        return ''

    return ' '.join(w.capitalize() for w in ascii_text.split())


def telugu_to_searchable(raw_telugu: str) -> str:
    """
    Return a combined ASCII-only string for search matching.
    Merges outputs from ITRANS, IAST and HK so that multiple common
    English spellings all match (e.g. Ramesh / Rames / Ramez).
    """
    text = clean_telugu_source(raw_telugu)
    if not text:
        return ''

    variants: set[str] = set()
    for scheme in (sanscript.ITRANS, sanscript.IAST, sanscript.HK):
        raw = _transliterate_scheme(text, scheme)
        if not raw:
            continue
        asc = _to_ascii(raw)
        asc = _fix_phonology(asc)
        if asc:
            variants.add(asc)

    return ' '.join(sorted(variants))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    input_file  = 'voters_raw.json'
    output_file = 'voters.json'

    print(f'Loading {input_file} …')
    with open(input_file, encoding='utf-8') as f:
        voters = json.load(f)

    print(f'Processing {len(voters)} voter records …')
    for i, v in enumerate(voters):
        raw_name     = v.get('voter_name', '')
        raw_rel_name = v.get('relation_name', '')

        # Also clean the Telugu source fields themselves
        v['voter_name']    = clean_telugu_source(raw_name)
        v['relation_name'] = clean_telugu_source(raw_rel_name)

        v['voter_name_display']    = telugu_to_display(raw_name)
        v['relation_name_display'] = telugu_to_display(raw_rel_name)
        v['voter_name_en']         = telugu_to_searchable(raw_name)
        v['relation_name_en']      = telugu_to_searchable(raw_rel_name)

        if (i + 1) % 500 == 0:
            print(f'  … {i + 1} / {len(voters)} done')

    print(f'Writing {output_file} …')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(voters, f, ensure_ascii=False, indent=2)

    # ── Verification report ──────────────────────────────────────────────────
    print('\n── Verification ───────────────────────────────────────────────────')
    test_names = [
        'మల్లికార్జున తన్నీరు',
        'గడ్డంం మాధవరావు\nమాధవరావు',
        'వెంకటరావు దడబడి',
        'శివకృష్ణ వడ్లమూడి',
        'శ్రీీరాములు పందిళ్ల',
        'రజని ఉన్నంం',
        'అనూష అక్కెలగుంట',
        'సాయి కుమార్ పాలేటి\nతల్లి పేరు\n: అరుణ పాలేటి',
        'శ్రాావణి గౌడపేరు',
        'హరికృష్ణ ఘట్టమనేని',
        'కొండయ్య ధదబడి',
        'రవణమ్మ కుంచల',
        'పొన్నగంటి నరసింహారావు',
        'కందుకూరి రమేశ్',
    ]
    for name in test_names:
        display = telugu_to_display(name)
        print(f'  {name!r}')
        print(f'  → {display!r}')
        print()

    # Count remaining artefacts
    mm_count  = sum(1 for v in voters if v.get('voter_name_display','').lower().endswith('mm'))
    vem_count = sum(1 for v in voters if 'vem' in v.get('voter_name_display','').lower())
    krr_count = sum(1 for v in voters if 'krr' in v.get('voter_name_display','').lower())
    ii_count  = sum(1 for v in voters if 'ii'  in v.get('voter_name_display','').lower())
    print(f'Remaining artefacts — mm-end:{mm_count}  vem:{vem_count}  krr:{krr_count}  ii:{ii_count}')
    print(f'\nDone! Total voters: {len(voters)}')


if __name__ == '__main__':
    main()
