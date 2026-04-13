

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Required keys every record must contain (subset check)
REQUIRED_KEYS = {
    "program_course_name",
    "university_name",
    "course_website_url",
    "study_level",
    "yearly_tuition_fee",
}


def validate_records(records: list[dict]) -> list[str]:
    warnings: list[str] = []

    if not records:
        warnings.append("No records to save.")
        return warnings

    for idx, record in enumerate(records, start=1):
        missing = REQUIRED_KEYS - record.keys()
        if missing:
            warnings.append(
                f"Record {idx} missing keys: {', '.join(sorted(missing))}"
            )
        if record.get("course_website_url", "NA") == "NA":
            warnings.append(f"Record {idx} has no course_website_url.")
        if record.get("program_course_name", "NA") == "NA":
            warnings.append(f"Record {idx} has no program_course_name.")

    return warnings


def save_output(records: list[dict], output_path: Path) -> None:
    # Validate first
    issues = validate_records(records)
    for issue in issues:
        logger.warning("Validation: %s", issue)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)

    logger.info("Output saved → %s  (%d record(s))", output_path, len(records))
