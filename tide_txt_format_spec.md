# Tide TXT Format Specification (for Codex)

## Overview
This document describes the fixed-width text format of the Japan Meteorological Agency
tide table data (hourly tide level with high/low tide times).

- Source file example: `2026_TK.txt`
- File format: plain text (.txt)
- Line separator: LF (`\n`)
- Encoding: ASCII / UTF-8 compatible (numeric data only)
- One line represents **one day for one observation station**
- Records are **fixed-width (column-based)**

This specification is intended for **programmatic parsing** (Python / JavaScript / PHP).

---

## Record Structure (Fixed Width)

Each line has **136 characters** and the following structure  
(1-based column index):

| Field | Columns | Length | Description |
|------|--------|--------|------------|
| Hourly tide levels | 1–72 | 72 | 24 hourly tide values (0–23h), 3 chars each |
| Date (YYMMDD) | 73–78 | 6 | Year, month, day |
| Station code | 79–80 | 2 | Alphanumeric station identifier |
| High tides (×4) | 81–108 | 28 | (Time HHMM + Height HHH) ×4 |
| Low tides (×4) | 109–136 | 28 | (Time HHMM + Height HHH) ×4 |

---

## Field Definitions

### 1. Hourly Tide Levels (Columns 1–72)
- Represents tide height for each hour from **00:00 to 23:00**
- Each hour occupies **3 characters**
- Unit: **centimeters (cm)**
- Values may be **negative**
- Parsing rule:
  - Extract 3 characters
  - `strip()` whitespace
  - Convert to integer

Example mapping:
- Hour 0 → columns 1–3
- Hour 1 → columns 4–6
- ...
- Hour 23 → columns 70–72

---

### 2. Date (Columns 73–78)
- Format: `YYMMDD`
- Example: `260101` → 2026-01-01
- Century handling:
  - For this project, assume **2000–2099**
  - Final date = `20YY-MM-DD`

---

### 3. Station Code (Columns 79–80)
- 2-character alphanumeric code
- Example:
  - `TK` = Tokyo
- Station name mapping is handled **outside this file**

---

### 4. High Tides (Columns 81–108)
- Up to **4 high tides per day**
- Each entry = **7 characters**
  - Time: 4 chars (`HHMM`)
  - Height: 3 chars (`HHH`, cm)

| Entry | Time | Height |
|------|------|--------|
| High tide 1 | 81–84 | 85–87 |
| High tide 2 | 88–91 | 92–94 |
| High tide 3 | 95–98 | 99–101 |
| High tide 4 | 102–105 | 106–108 |

#### Missing value rule
- If a high tide is not predicted:
  - Time = `9999`
  - Height = `999`
- These should be treated as **null / ignored** in code

---

### 5. Low Tides (Columns 109–136)
- Same structure as high tides

| Entry | Time | Height |
|------|------|--------|
| Low tide 1 | 109–112 | 113–115 |
| Low tide 2 | 116–119 | 120–122 |
| Low tide 3 | 123–126 | 127–129 |
| Low tide 4 | 130–133 | 134–136 |

#### Missing value rule
- Time = `9999`
- Height = `999`
- Treat as **null / ignored**

---

## Parsing Guidelines (Important)
1. Read file **line by line**
2. For each line:
   - `rstrip("\n")`
   - Slice by fixed column positions
3. Convert numeric fields using `int()`
4. Handle missing values (`9999`, `999`) explicitly
5. Do **not** modify the original TXT file (TXT is the authoritative source)

---

## Recommended Parsed Data Model (Conceptual)

- `date`: YYYY-MM-DD
- `station_code`: string
- `hourly_tides`: array of 24 integers (cm)
- `high_tides`: list of `{ time: "HHMM", height_cm: int }`
- `low_tides`: list of `{ time: "HHMM", height_cm: int }`

---

## Notes
- The TXT file itself is the **primary data source**
- This specification exists solely to make the structure explicit for code generation
- Any future additional rules should be appended here, not inferred in code

