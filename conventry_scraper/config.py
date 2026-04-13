

import os
from pathlib import Path

# ── Output ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(os.getenv("SCRAPER_OUTPUT_DIR", "output"))
OUTPUT_FILENAME = os.getenv("SCRAPER_OUTPUT_FILE", "coventry_courses.json")
OUTPUT_PATH = OUTPUT_DIR / OUTPUT_FILENAME

# ── Crawl behaviour ─────────────────────────────────────────────────────────
MAX_COURSES: int = 5          # number of course records to collect
REQUEST_DELAY: float = 1.5    # seconds between requests (polite crawling)
REQUEST_TIMEOUT: int = 20     # per-request timeout in seconds

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s  %(levelname)-8s  %(message)s"
LOG_DATE_FORMAT: str = "%H:%M:%S"
