#!/usr/bin/env python3
"""
extract_voters_v2.py
Re-extracts voter data from the PDF using PyMuPDF for clean Telugu Unicode.
Outputs: voters_raw.json (raw data, no transliteration yet)

Run: python3 extract_voters_v2.py
Then: python3 add_transliteration.py  (to add English display names)
"""

import re
import json
import fitz  # PyMuPDF

PDF_FILE  = "Sakhavaram Final 2026.pdf"
OUTPUT    = "voters_raw.json"

# --- Patterns ---
# గ్రాా.పం.ఓ.జా.వ.సం . \xa0 <part_serial> \xa0
# అ.ఓ.జా.వ.సం .109 - 26 - 1
#   group(1) = voter seq no (part_serial: 1,2,3...)
#   group(2) = ward no (109 for all — Kandukuri constituency)
#   group(3) = part no within ward (24,25,26...)
#   group(4) = voter serial within part (unique per part)
BLOCK_SPLIT = re.compile(
    r'గ్రాా?\.పం\.ఓ\.జా\.వ\.సం\s*\.\s*[\xa0\s]*(\d+)[\xa0\s]*'
    r'అ\.ఓ\.జా\.వ\.సం\s*\.?\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)'
)
VOTER_ID_PAT = re.compile(r'\b([A-Z]{3}\d{7})\b')


def clean(s: str) -> str:
    """Strip \xa0, extra spaces, and leading/trailing whitespace."""
    s = s.replace('\xa0', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()


def after_label(text, labels, stop_labels=None):
    """Return the value that follows the first matching label."""
    for label in labels:
        idx = text.find(label)
        if idx == -1:
            continue
        start = idx + len(label)
        # skip colon / space
        while start < len(text) and text[start] in (' ', ':', '\t', '\n', '\xa0'):
            start += 1
        end = len(text)
        if stop_labels:
            for sl in stop_labels:
                si = text.find(sl, start)
                if si != -1 and si < end:
                    end = si
        return clean(text[start:end])
    return ""


# Telugu field labels as they appear in PyMuPDF output
VOTER_NAME_L   = ["ఓటరు పేరు"]
FATHER_L       = ["తండ్రిి పేరు", "తండ్రి పేరు", "తండి పేరు", "తం డి పేరు"]
HUSBAND_L      = ["భర్తుు పేరు", "భర్తు పేరు", "భర్త పేరు", "భర పేరు", "భర్తపేరు", "భరతు పేరు", "భర్తిి పేరు"]
AGE_L          = ["వయస్సు", "వయసు", "వయస్"]
GENDER_L       = ["లింగము"]
HOUSE_L        = ["ఇంటి సంఖ్య", "ఇంటి సంఖ"]
VOTER_ID_L     = ["ఓటరు ఐడి. కార్డు నెం.", "ఓటరు ఐడి. కారు నెం.", "ఓటరు ఐడి.కారు నెం."]


def parse_block(part_serial, full_serial, block):
    """Parse a single voter text block."""
    # Voter name
    voter_name = after_label(block, VOTER_NAME_L,
        FATHER_L + HUSBAND_L + AGE_L + GENDER_L + HOUSE_L + VOTER_ID_L)

    # Relation
    relation_type = ""
    relation_name = ""
    father = after_label(block, FATHER_L, HUSBAND_L + AGE_L + GENDER_L + HOUSE_L + VOTER_ID_L)
    if father:
        relation_type = "తండ్రి"
        relation_name = father
    else:
        husband = after_label(block, HUSBAND_L, AGE_L + GENDER_L + HOUSE_L + VOTER_ID_L)
        if husband:
            relation_type = "భర్త"
            relation_name = husband

    # Age
    age_raw = after_label(block, AGE_L, GENDER_L + HOUSE_L + VOTER_ID_L)
    age = re.sub(r'\D', '', age_raw.split()[0]) if age_raw else ""

    # Gender
    gender_raw = after_label(block, GENDER_L, HOUSE_L + VOTER_ID_L)
    gender_raw = gender_raw.strip()
    if "పు" in gender_raw or "Male" in gender_raw or "పురు" in gender_raw:
        gender = "Male"
    elif gender_raw and gender_raw not in ["", "0"]:
        gender = "Female"
    else:
        gender = ""

    # House
    house = after_label(block, HOUSE_L, VOTER_ID_L + ["ఓటరు ఐడి"])

    # Voter ID - regex is most reliable
    id_match = VOTER_ID_PAT.search(block)
    voter_id = id_match.group(1) if id_match else ""

    if not voter_name and not voter_id:
        return None

    return {
        "part_serial":   part_serial,
        "full_serial":   full_serial,
        "voter_name":    voter_name,
        "relation_type": relation_type,
        "relation_name": relation_name,
        "age":           age,
        "gender":        gender,
        "house_number":  house,
        "voter_id":      voter_id,
    }


def extract_all() -> list[dict]:
    voters = []
    doc = fitz.open(PDF_FILE)
    total = len(doc)
    print(f"Opened '{PDF_FILE}' — {total} pages")

    for page_num in range(total):
        page = doc[page_num]
        text = page.get_text()

        if page_num % 10 == 0:
            print(f"  Page {page_num}/{total}  voters so far: {len(voters)}")

        # Find all voter block boundaries
        matches = list(BLOCK_SPLIT.finditer(text))
        if not matches:
            continue

        for i, m in enumerate(matches):
            seq_no      = m.group(1)                    # 1, 2, 3 … 2208
            ward_no     = m.group(2)                    # 109 (same for all)
            part_no     = m.group(3)                    # 24 / 25 / 26
            serial_in_part = m.group(4)                 # voter's serial within part
            full_serial = f"{ward_no}-{part_no}-{serial_in_part}"  # e.g. 109-26-1

            # Block text: from after the serial header to next match (or end)
            block_start = m.end()
            block_end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block       = text[block_start:block_end]

            voter = parse_block(seq_no, full_serial, block)
            if voter:
                voters.append(voter)

    doc.close()
    return voters


if __name__ == "__main__":
    print("=== Sakhavaram 2026 — Re-extraction with PyMuPDF ===\n")
    voters = extract_all()
    print(f"\nTotal voters extracted: {len(voters)}")

    if voters:
        # Deduplicate by voter_id (keep last occurrence which tends to be cleaner)
        seen_ids: dict[str, dict] = {}
        seen_serials: set[str] = set()
        deduped = []
        for v in voters:
            key = v["voter_id"] or v["part_serial"]
            if key and key not in seen_ids:
                seen_ids[key] = v
                deduped.append(v)
            elif not key:
                deduped.append(v)

        print(f"After dedup: {len(deduped)}")

        # Sort by part_serial
        deduped.sort(key=lambda v: int(v["part_serial"]) if v["part_serial"].isdigit() else 999999)

        # Sample output
        print("\nSample (first 5):")
        for v in deduped[:5]:
            print(f"  [{v['part_serial']}] {v['voter_name']} | {v['relation_name']} | {v['voter_id']}")

        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(deduped, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(deduped)} voters → {OUTPUT}")
    else:
        print("No voters found!")
