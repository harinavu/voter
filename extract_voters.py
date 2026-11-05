#!/usr/bin/env python3
"""
Extract voter data from Sakhavaram 2026 voter roll PDF.
Outputs: voters.xlsx and voters.json
"""

import re
import json
import pdfplumber
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PDF_FILE = "Sakhavaram Final 2026.pdf"
OUTPUT_EXCEL = "voters.xlsx"
OUTPUT_JSON = "voters.json"

# Telugu labels to identify fields
VOTER_NAME_LABELS   = ["ఓటరు పేరు", "ఓటర్ పేరు"]
FATHER_NAME_LABELS  = ["తండ్రి పేరు", "తండి పేరు", "తండి పేరు"]
HUSBAND_NAME_LABELS = ["భర్త పేరు", "భర పేరు", "భర్తపేరు"]
AGE_LABELS          = ["వయసు", "వయస్సు"]
GENDER_LABELS       = ["లింగము", "లింగం"]
HOUSE_LABELS        = ["ఇంటి సంఖ్య", "ఇంటి సంఖ"]
VOTER_ID_LABELS     = ["ఓటరు ఐడి. కారు నెం.", "ఓటరు ఐడి. కారు నెం", "ఓటరు ఐడి.కారు నెం."]

SERIAL_PATTERN = re.compile(
    r'(?:గా\.పం\.ఓ\.జా\.వ\.సం\s*[.\s]*|గా\.పం\.ఓ\.జా\.వ\.స\s*[.\s]*)\s*(\d+)\s+'
    r'అ\.ఓ\.జా\.వ\.సం\s*[.\s]*\s*([\d\-]+)'
)

VOTER_ID_PATTERN = re.compile(r'\b([A-Z]{3}\d{7})\b')

def clean(text):
    """Remove null bytes and extra whitespace."""
    if not text:
        return ""
    return re.sub(r'\x00+', '', text).strip()

def extract_field(text, labels, stop_labels=None):
    """Extract value after a label up to the next label or end."""
    for label in labels:
        idx = text.find(label)
        if idx != -1:
            value_start = idx + len(label)
            # Skip : and spaces
            while value_start < len(text) and text[value_start] in [' ', ':', '\t']:
                value_start += 1
            # Find where value ends
            value_end = len(text)
            if stop_labels:
                for sl in stop_labels:
                    si = text.find(sl, value_start)
                    if si != -1 and si < value_end:
                        value_end = si
            return clean(text[value_start:value_end])
    return ""

def parse_voter_block(block_text):
    """Parse a single voter block into a dict."""
    block_text = clean(block_text)
    
    # Extract serial numbers
    serial_match = SERIAL_PATTERN.search(block_text)
    part_serial = serial_match.group(1) if serial_match else ""
    full_serial = serial_match.group(2) if serial_match else ""
    
    # Extract voter ID using regex
    voter_id_match = VOTER_ID_PATTERN.search(block_text)
    voter_id = voter_id_match.group(1) if voter_id_match else ""
    
    # Extract voter name
    voter_name = extract_field(block_text, VOTER_NAME_LABELS,
                               FATHER_NAME_LABELS + HUSBAND_NAME_LABELS + AGE_LABELS + GENDER_LABELS + HOUSE_LABELS)
    
    # Extract relation name (father or husband)
    relation_type = ""
    relation_name = ""
    father_name = extract_field(block_text, FATHER_NAME_LABELS,
                                HUSBAND_NAME_LABELS + AGE_LABELS + GENDER_LABELS + HOUSE_LABELS)
    if father_name:
        relation_type = "తండ్రి"
        relation_name = father_name
    else:
        husband_name = extract_field(block_text, HUSBAND_NAME_LABELS,
                                     AGE_LABELS + GENDER_LABELS + HOUSE_LABELS)
        if husband_name:
            relation_type = "భర్త"
            relation_name = husband_name
    
    # Extract age
    age_raw = extract_field(block_text, AGE_LABELS, GENDER_LABELS + HOUSE_LABELS)
    age = re.sub(r'\D', '', age_raw.split()[0]) if age_raw else ""
    
    # Extract gender
    gender_raw = extract_field(block_text, GENDER_LABELS, HOUSE_LABELS + VOTER_ID_LABELS)
    gender_raw = gender_raw.strip()
    if "పు" in gender_raw or "Male" in gender_raw or "పురు" in gender_raw:
        gender = "Male"
    elif gender_raw and gender_raw not in ["", "0"]:
        gender = "Female"
    else:
        gender = ""
    
    # Extract house number
    house = extract_field(block_text, HOUSE_LABELS, VOTER_ID_LABELS + ["ఓటరు ఐడి"])
    
    return {
        "part_serial": part_serial,
        "full_serial": full_serial,
        "voter_name": voter_name,
        "relation_type": relation_type,
        "relation_name": relation_name,
        "age": age,
        "gender": gender,
        "house_number": house,
        "voter_id": voter_id,
    }

def extract_voters():
    voters = []
    
    print(f"Opening {PDF_FILE}...")
    with pdfplumber.open(PDF_FILE) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        # Skip first 2 pages (cover + summary)
        for page_num in range(2, total_pages):
            page = pdf.pages[page_num]
            
            if page_num % 10 == 0:
                print(f"  Processing page {page_num}/{total_pages}, voters so far: {len(voters)}")
            
            # Extract tables (each voter is in a table cell)
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        for cell in row:
                            if cell and "ఓటరు పేరు" in str(cell):
                                voter = parse_voter_block(str(cell))
                                if voter["voter_name"] or voter["voter_id"]:
                                    voters.append(voter)
            else:
                # Fallback: parse raw text
                text = page.extract_text() or ""
                # Split into blocks by voter serial pattern
                blocks = re.split(r'(?=గా\.పం\.ఓ\.జా\.వ\.సం)', text)
                for block in blocks:
                    if "ఓటరు పేరు" in block:
                        voter = parse_voter_block(block)
                        if voter["voter_name"] or voter["voter_id"]:
                            voters.append(voter)
    
    return voters

def save_excel(voters):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Voters"
    
    # Header style
    header_fill = PatternFill(start_color="1E3A5F", end_color="1E3A5F", fill_type="solid")
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=12)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    # Data style alternate rows
    even_fill = PatternFill(start_color="EAF2FB", end_color="EAF2FB", fill_type="solid")
    odd_fill  = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    data_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    
    headers = [
        "S.No",
        "Part Serial No.",
        "Full Serial No.",
        "Voter Name (Telugu)",
        "Relation Type",
        "Relation Name (Telugu)",
        "Age",
        "Gender",
        "House Number",
        "Voter ID",
    ]
    
    col_widths = [6, 14, 14, 30, 14, 30, 8, 10, 14, 14]
    
    for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    
    for row_idx, voter in enumerate(voters, start=2):
        fill = even_fill if row_idx % 2 == 0 else odd_fill
        values = [
            row_idx - 1,
            voter["part_serial"],
            voter["full_serial"],
            voter["voter_name"],
            voter["relation_type"],
            voter["relation_name"],
            voter["age"],
            voter["gender"],
            voter["house_number"],
            voter["voter_id"],
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.fill = fill
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[row_idx].height = 20
    
    # Auto-filter
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"
    
    wb.save(OUTPUT_EXCEL)
    print(f"Saved Excel: {OUTPUT_EXCEL} ({len(voters)} voters)")

def save_json(voters):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(voters, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON: {OUTPUT_JSON} ({len(voters)} voters)")

if __name__ == "__main__":
    print("=== Sakhavaram 2026 Voter Roll Extractor ===")
    voters = extract_voters()
    print(f"\nTotal voters extracted: {len(voters)}")
    
    if voters:
        # Show sample
        print("\nSample voters (first 3):")
        for v in voters[:3]:
            print(f"  {v['voter_id']} - {v['voter_name']} - Age:{v['age']} - {v['gender']}")
        
        save_excel(voters)
        save_json(voters)
        print("\nDone!")
    else:
        print("No voters found! Check the PDF structure.")
