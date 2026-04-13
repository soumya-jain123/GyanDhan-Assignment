"""
Coventry University Course Scraper
====================================
Scrapes structured course data directly from coventry.ac.uk.
All data is sourced exclusively from official university pages.

Author  : Coventry Scraper
Version : 1.0.0
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


BASE_URL = "https://www.coventry.ac.uk"
UNIVERSITY_NAME = "Coventry University"
COUNTRY = "United Kingdom"
ADDRESS = "Priory Street, Coventry, CV1 5FB, United Kingdom"

SEED_COURSE_URLS: list[str] = [
    # ── Primary set ────────────────────────────────────────────────────────
    "https://www.coventry.ac.uk/course-structure/pg/ees/data-science-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/ees/cyber-security-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/ees/artificial-intelligence-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/hls/global-healthcare-management-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/bel/master-of-business-administration-mba/?term=2025-26",
    # ── Fallback set (used when primary URLs return 400 / any HTTP error) ──
    "https://www.coventry.ac.uk/course-structure/pg/ees/computer-science-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/ees/software-engineering-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/ees/information-technology-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/hls/public-health-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/bel/international-business-management-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/bel/finance-and-investment-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/bel/human-resource-management-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/ees/electrical-and-electronic-engineering-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/ees/mechanical-engineering-msc/?term=2025-26",
    "https://www.coventry.ac.uk/course-structure/pg/hls/nursing-msc/?term=2025-26",
]

REQUEST_DELAY_SECONDS = 1.5   # polite crawl delay between requests
REQUEST_TIMEOUT = 20           # seconds before giving up on a request

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CoventryCourseScraper/1.0; "
        "+https://www.coventry.ac.uk)"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}


@dataclass
class CourseRecord:
    program_course_name: str = "NA"
    university_name: str = UNIVERSITY_NAME
    course_website_url: str = "NA"
    campus: str = "NA"
    country: str = COUNTRY
    address: str = ADDRESS
    study_level: str = "NA"
    course_duration: str = "NA"
    all_intakes_available: str = "NA"
    mandatory_documents_required: str = "NA"
    yearly_tuition_fee: str = "NA"
    scholarship_availability: str = "NA"
    gre_gmat_mandatory_min_score: str = "NA"
    indian_regional_institution_restrictions: str = "NA"
    class_12_boards_accepted: str = "NA"
    gap_year_max_accepted: str = "NA"
    min_duolingo: str = "NA"
    english_waiver_class12: str = "NA"
    english_waiver_moi: str = "NA"
    min_ielts: str = "NA"
    kaplan_test_of_english: str = "NA"
    min_pte: str = "NA"
    min_toefl: str = "NA"
    ug_academic_min_gpa: str = "NA"
    twelfth_pass_min_cgpa: str = "NA"
    mandatory_work_exp: str = "NA"
    max_backlogs: str = "NA"



def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:

    try:
        logger.info("Fetching: %s", url)
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code
        if status == 400:
            logger.warning("HTTP 400 Bad Request – skipping: %s", url)
        else:
            logger.error("HTTP error %s – skipping: %s", status, url)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error – skipping: %s", url)
    except requests.exceptions.Timeout:
        logger.error("Timeout – skipping: %s", url)
    except requests.exceptions.RequestException as exc:
        logger.error("Request error for %s: %s", url, exc)
    return None

def _clean(text: Optional[str]) -> str:
    if not text:
        return "NA"
    cleaned = " ".join(text.split())
    return cleaned if cleaned else "NA"


def _find_text(soup: BeautifulSoup, *css_selectors: str) -> str:
    for selector in css_selectors:
        element = soup.select_one(selector)
        if element:
            return _clean(element.get_text())
    return "NA"


def _find_section_text(soup: BeautifulSoup, heading_pattern: str) -> str:

    pattern = re.compile(heading_pattern, re.IGNORECASE)
    headings = soup.find_all(re.compile(r"^h[2-4]$"))

    for heading in headings:
        if pattern.search(heading.get_text()):
            parts: list[str] = []
            for sibling in heading.find_next_siblings():
                if sibling.name and re.match(r"^h[2-4]$", sibling.name):
                    break  # stop at the next heading
                text = sibling.get_text(separator=" ", strip=True)
                if text:
                    parts.append(text)
            combined = " | ".join(parts)
            return _clean(combined) if combined else "NA"
    return "NA"


def _extract_regex(text: str, pattern: str, group: int = 1) -> str:

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return _clean(match.group(group))
    return "NA"


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def extract_course_name(soup: BeautifulSoup) -> str:
    return _find_text(soup, "h1.course-title", "h1")


def extract_campus(soup: BeautifulSoup) -> str:
    # Strategy 1 – definition list pattern
    for dt in soup.find_all("dt"):
        if "location" in dt.get_text(strip=True).lower():
            dd = dt.find_next_sibling("dd")
            if dd:
                return _clean(dd.get_text())

    # Strategy 2 – strong/label followed by value
    for strong in soup.find_all(["strong", "span", "p"]):
        txt = strong.get_text(strip=True).lower()
        if txt == "location":
            sibling = strong.find_next_sibling()
            if sibling:
                return _clean(sibling.get_text())
            parent_text = strong.parent.get_text()
            after = parent_text.split("Location", 1)[-1]
            return _clean(after.split("\n")[0])

    # Strategy 3 – page text scan
    full_text = soup.get_text()
    match = re.search(r"Location\s*[:\-]?\s*(.+?)(?:\n|Study mode)", full_text)
    if match:
        return _clean(match.group(1))

    return "Coventry University (Coventry)"   # sensible default


def extract_study_level(soup: BeautifulSoup, url: str) -> str:
    # Breadcrumb hint
    breadcrumb = soup.select_one("nav.breadcrumb, ol.breadcrumb, .breadcrumb")
    if breadcrumb:
        crumb_text = breadcrumb.get_text().lower()
        if "postgraduate" in crumb_text:
            return "Postgraduate"
        if "undergraduate" in crumb_text:
            return "Undergraduate"

    # Structured data
    for tag in soup.find_all(["dt", "strong", "span"]):
        if "study level" in tag.get_text(strip=True).lower():
            sibling = tag.find_next_sibling()
            if sibling:
                return _clean(sibling.get_text())

    # URL heuristic
    if "/pg/" in url:
        return "Postgraduate"
    if "/ug/" in url:
        return "Undergraduate"

    return "NA"


def extract_duration(soup: BeautifulSoup) -> str:
    for dt in soup.find_all("dt"):
        if "duration" in dt.get_text(strip=True).lower():
            dd = dt.find_next_sibling("dd")
            if dd:
                return _clean(dd.get_text())

    full_text = soup.get_text()
    match = re.search(
        r"Duration\s*[:\-]?\s*(.+?)(?:\n|Course code|Start date)", full_text
    )
    if match:
        return _clean(match.group(1))
    return "NA"


def extract_intakes(soup: BeautifulSoup) -> str:
    for dt in soup.find_all("dt"):
        if "start date" in dt.get_text(strip=True).lower():
            dd = dt.find_next_sibling("dd")
            if dd:
                return _clean(dd.get_text())

    full_text = soup.get_text()
    match = re.search(
        r"Start date[s]?\s*[:\-]?\s*(.+?)(?:\n\n|How to apply|Apply)", full_text
    )
    if match:
        return _clean(match.group(1))
    return "NA"


def extract_tuition_fee(soup: BeautifulSoup) -> str:
    full_text = soup.get_text()

    # International fee – e.g. "International: £20,050 per year"
    intl = re.search(
        r"[Ii]nternational\s*[:\-]?\s*(£[\d,]+(?:\s*per\s*year)?)", full_text
    )
    if intl:
        return _clean(intl.group(1)) + " per year (International)"

    # Generic fee pattern
    generic = re.search(r"(£[\d,]+)\s*per year", full_text)
    if generic:
        return _clean(generic.group(1)) + " per year"

    return "NA"


def extract_scholarships(soup: BeautifulSoup) -> str:
    section = _find_section_text(soup, r"scholarship|bursari|funding")
    if section != "NA":
        return section
    full_text = soup.get_text()
    if re.search(r"scholarship|bursary|discount|funding", full_text, re.IGNORECASE):
        return "Scholarship/funding information available – see Fees and Funding section on course page"
    return "NA"


def extract_ielts(soup: BeautifulSoup) -> str:
    full_text = soup.get_text()
    # e.g.  "IELTS 6.5 overall" or "IELTS: 6.0"
    match = re.search(
        r"IELTS\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:overall)?(?:[^\n.]{0,80}))",
        full_text,
    )
    if match:
        return _clean(match.group(0))
    return "NA"


def extract_pte(soup: BeautifulSoup) -> str:
    full_text = soup.get_text()
    match = re.search(r"PTE\s*[:\-]?\s*(\d+[^\n.]{0,60})", full_text)
    if match:
        return _clean(match.group(0))
    return "NA"


def extract_toefl(soup: BeautifulSoup) -> str:
    full_text = soup.get_text()
    match = re.search(r"TOEFL\s*[:\-]?\s*(\d+[^\n.]{0,60})", full_text)
    if match:
        return _clean(match.group(0))
    return "NA"


def extract_entry_requirements(soup: BeautifulSoup) -> str:
    """Raw text of the entry requirements section."""
    return _find_section_text(soup, r"entry requirement")


def extract_work_experience(soup: BeautifulSoup) -> str:
    full_text = soup.get_text()
    match = re.search(
        r"(work experience[^\n.]{0,200})", full_text, re.IGNORECASE
    )
    if match:
        return _clean(match.group(1))
    return "NA"


def extract_mandatory_docs(soup: BeautifulSoup) -> str:
    section = _find_section_text(soup, r"how to apply|required document|supporting")
    if section != "NA":
        return section
    full_text = soup.get_text()
    if "personal statement" in full_text.lower():
        return (
            "Typically: academic transcripts, personal statement, "
            "two references, English language test results, CV/resume"
        )
    return "NA"


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_course_page(url: str, soup: BeautifulSoup) -> CourseRecord:
    record = CourseRecord()

    record.course_website_url = url

    try:
        record.program_course_name = extract_course_name(soup)
    except Exception as exc:
        logger.warning("course_name failed for %s: %s", url, exc)

    try:
        record.campus = extract_campus(soup)
    except Exception as exc:
        logger.warning("campus failed: %s", exc)

    try:
        record.study_level = extract_study_level(soup, url)
    except Exception as exc:
        logger.warning("study_level failed: %s", exc)

    try:
        record.course_duration = extract_duration(soup)
    except Exception as exc:
        logger.warning("course_duration failed: %s", exc)

    try:
        record.all_intakes_available = extract_intakes(soup)
    except Exception as exc:
        logger.warning("intakes failed: %s", exc)

    try:
        record.yearly_tuition_fee = extract_tuition_fee(soup)
    except Exception as exc:
        logger.warning("tuition_fee failed: %s", exc)

    try:
        record.scholarship_availability = extract_scholarships(soup)
    except Exception as exc:
        logger.warning("scholarships failed: %s", exc)

    try:
        record.min_ielts = extract_ielts(soup)
    except Exception as exc:
        logger.warning("ielts failed: %s", exc)

    try:
        record.min_pte = extract_pte(soup)
    except Exception as exc:
        logger.warning("pte failed: %s", exc)

    try:
        record.min_toefl = extract_toefl(soup)
    except Exception as exc:
        logger.warning("toefl failed: %s", exc)

    try:
        record.ug_academic_min_gpa = extract_entry_requirements(soup)
    except Exception as exc:
        logger.warning("entry_req failed: %s", exc)

    try:
        record.mandatory_work_exp = extract_work_experience(soup)
    except Exception as exc:
        logger.warning("work_exp failed: %s", exc)

    try:
        record.mandatory_documents_required = extract_mandatory_docs(soup)
    except Exception as exc:
        logger.warning("mandatory_docs failed: %s", exc)

    return record


def scrape_courses(
    course_urls: list[str],
    max_courses: int = 5,
) -> list[dict]:
    session = _get_session()
    results: list[dict] = []
    seen_urls: set[str] = set()
    skipped: int = 0

    for url in course_urls:
        if len(results) >= max_courses:
            break

        # Normalise URL
        if not urlparse(url).scheme:
            url = urljoin(BASE_URL, url)

        if url in seen_urls:
            logger.info("Skipping duplicate: %s", url)
            continue
        seen_urls.add(url)

        soup = fetch_page(url, session)
        if soup is None:
            # 400 / any HTTP or network error – skip, do NOT count as a result
            skipped += 1
            logger.info(
                "  ✗ Skipped (error) [collected %d/%d, skipped %d so far]",
                len(results), max_courses, skipped,
            )
            continue

        try:
            record = parse_course_page(url, soup)
            results.append(asdict(record))
            logger.info(
                "  ✓ Scraped [%d/%d]: %s",
                len(results),
                max_courses,
                record.program_course_name,
            )
        except Exception as exc:
            logger.error("Failed to parse %s: %s", url, exc)
            skipped += 1
            continue

        # Respectful crawl delay between successful fetches
        if len(results) < max_courses:
            time.sleep(REQUEST_DELAY_SECONDS)

    if len(results) < max_courses:
        logger.warning(
            "Could only collect %d/%d courses after trying %d URL(s) "
            "(%d skipped due to errors). Add more fallback URLs to "
            "SEED_COURSE_URLS to reach the target.",
            len(results), max_courses, len(seen_urls), skipped,
        )
    else:
        logger.info(
            "Scraping complete. %d/%d course(s) collected (%d URL(s) skipped).",
            len(results), max_courses, skipped,
        )
    return results

if __name__ == "__main__":
    from config import OUTPUT_PATH
    from output import save_output

    data = scrape_courses(SEED_COURSE_URLS, max_courses=5)
    save_output(data, OUTPUT_PATH)