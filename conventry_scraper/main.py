

from __future__ import annotations

import logging
import sys

from config import LOG_DATE_FORMAT, LOG_FORMAT, LOG_LEVEL, MAX_COURSES, OUTPUT_PATH
from output import save_output
from scraper import SEED_COURSE_URLS, scrape_courses


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("  Coventry University Course Scraper  v1.0.0")
    logger.info("=" * 60)
    logger.info("Target: %d courses from coventry.ac.uk", MAX_COURSES)

    try:
        records = scrape_courses(SEED_COURSE_URLS, max_courses=MAX_COURSES)
    except Exception as exc:
        logger.error("Scraping pipeline failed: %s", exc, exc_info=True)
        return 1

    if not records:
        logger.error("No records were collected. Aborting.")
        return 1

    try:
        save_output(records, OUTPUT_PATH)
    except OSError as exc:
        logger.error("Could not write output: %s", exc)
        return 1

    logger.info("Done. Check '%s' for results.", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
