# Coventry University Course Scraper

A production-ready Python scraper that extracts structured course data
directly from [coventry.ac.uk](https://www.coventry.ac.uk/).

> **All data is sourced exclusively from official Coventry University web pages.
> No third-party platforms, pre-existing datasets, or manual copy-pasting are used.**

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Setup](#setup)
4. [How to Run](#how-to-run)
5. [Configuration](#configuration)
6. [Output Format](#output-format)
7. [How the Scraper Works](#how-the-scraper-works)
8. [Design Decisions](#design-decisions)
9. [Troubleshooting](#troubleshooting)

---

## Project Structure

```
coventry_scraper/
├── main.py            # Entry point – run this file
├── scraper.py         # Core scraping + extraction logic
├── config.py          # Tunable runtime settings
├── output.py          # Serialisation, validation, file I/O
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── output/
    └── coventry_courses.json   # Generated output (created on run)
```

---

## Prerequisites

| Requirement | Version |
| ----------- | ------- |
| Python      | 3.9 +   |
| pip         | any     |

---

## Setup

```bash
# 1. Clone / download the project
cd coventry_scraper

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to Run

```bash
python main.py
```

The script will:

1. Fetch 5 course pages from `coventry.ac.uk`
2. Parse and extract all required fields
3. Save the result to `output/coventry_courses.json`

**Expected console output:**

```
13:00:01  INFO    ============================================================
13:00:01  INFO      Coventry University Course Scraper  v1.0.0
13:00:01  INFO    ============================================================
13:00:01  INFO    Target: 5 courses from coventry.ac.uk
13:00:01  INFO    Fetching: https://www.coventry.ac.uk/course-structure/...
13:00:03  INFO      ✓ Scraped [1/5]: Data Science MSc
...
13:00:12  INFO    Scraping complete. 5 course(s) collected.
13:00:12  INFO    Output saved → output/coventry_courses.json  (5 record(s))
13:00:12  INFO    Done. Check 'output/coventry_courses.json' for results.
```

---

## Configuration

Edit `config.py` to change behaviour without touching scraper logic:

| Setting           | Default                 | Description                         |
| ----------------- | ----------------------- | ----------------------------------- |
| `MAX_COURSES`     | `5`                     | Number of courses to scrape         |
| `REQUEST_DELAY`   | `1.5`                   | Seconds between requests            |
| `REQUEST_TIMEOUT` | `20`                    | Per-request timeout (seconds)       |
| `OUTPUT_DIR`      | `output/`               | Where to save JSON                  |
| `OUTPUT_FILENAME` | `coventry_courses.json` | Output file name                    |
| `LOG_LEVEL`       | `INFO`                  | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Environment variables override config:

```bash
LOG_LEVEL=DEBUG python main.py
SCRAPER_OUTPUT_DIR=/tmp python main.py
```

---

## Output Format

The output is a **JSON array** of exactly 5 objects.
Each object follows this schema:

```json
{
  "program_course_name": "Data Science MSc",
  "university_name": "Coventry University",
  "course_website_url": "https://www.coventry.ac.uk/...",
  "campus": "Coventry University (Coventry)",
  "country": "United Kingdom",
  "address": "Priory Street, Coventry, CV1 5FB, UK",
  "study_level": "Postgraduate",
  "course_duration": "1 year full-time",
  "all_intakes_available": "March 2026 | May 2026 | July 2026",
  "mandatory_documents_required": "Academic transcripts, personal statement...",
  "yearly_tuition_fee": "£20,050 per year (International)",
  "scholarship_availability": "Global Scholarship and Early Payment Discount...",
  "gre_gmat_mandatory_min_score": "NA",
  "indian_regional_institution_restrictions": "NA",
  "class_12_boards_accepted": "NA",
  "gap_year_max_accepted": "NA",
  "min_duolingo": "NA",
  "english_waiver_class12": "NA",
  "english_waiver_moi": "NA",
  "min_ielts": "IELTS 6.0 overall...",
  "kaplan_test_of_english": "NA",
  "min_pte": "NA",
  "min_toefl": "NA",
  "ug_academic_min_gpa": "Normally a minimum 2:2 honours degree...",
  "twelfth_pass_min_cgpa": "NA",
  "mandatory_work_exp": "Not mandatory...",
  "max_backlogs": "NA"
}
```

**Field notes:**

- Fields not available on the page are set to `"NA"`.
- Raw text is captured as-is; no normalisation is applied (as per assignment guidelines).
- `course_website_url` always points to the final official page on `coventry.ac.uk`.
- `yearly_tuition_fee` shows the international fee where available, since this is most relevant for the assignment context.

---

## How the Scraper Works

```
main.py
  └── scrape_courses()          [scraper.py]
        ├── fetch_page()        HTTP GET with retry-safe session
        │     └── BeautifulSoup parse (lxml backend)
        └── parse_course_page() per-field extraction
              ├── extract_course_name()
              ├── extract_campus()
              ├── extract_study_level()
              ├── extract_duration()
              ├── extract_intakes()
              ├── extract_tuition_fee()
              ├── extract_scholarships()
              ├── extract_ielts()
              ├── extract_pte()
              ├── extract_toefl()
              ├── extract_entry_requirements()
              ├── extract_work_experience()
              └── extract_mandatory_docs()
```

Each extractor is wrapped in its own `try/except` – a failure in one field
never blocks extraction of any other field.

---

## Design Decisions

| Decision                                    | Reason                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `requests` + `BeautifulSoup` over Selenium  | Coventry's course pages are server-side rendered; no JS execution needed for the required fields |
| `lxml` parser                               | Faster and more lenient than `html.parser` on malformed markup                                   |
| `@dataclass` for `CourseRecord`             | Type-safe, auto-serialises via `asdict()`, easy to extend                                        |
| Per-field isolation with `try/except`       | Production resilience – one broken selector never kills the whole record                         |
| Polite crawl delay (`REQUEST_DELAY = 1.5s`) | Respectful crawling; avoids triggering rate-limiting                                             |
| Seed URLs with `?term=2025-26`              | Targets the current academic year to ensure up-to-date data                                      |

---

## Troubleshooting

| Symptom                 | Fix                                                                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `Connection error`      | Check your internet connection; ensure `coventry.ac.uk` is accessible                                                    |
| `No records collected`  | Verify the seed URLs in `scraper.py` still resolve (the university may restructure URLs)                                 |
| Fields returning `"NA"` | The page structure may have changed – inspect the live page and update the relevant `extract_*` function in `scraper.py` |
| `ModuleNotFoundError`   | Run `pip install -r requirements.txt`                                                                                    |
| Output not created      | Check write permissions on the `output/` directory                                                                       |
