"""Run the source, cleaning, analysis, report, and chart pipeline."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Dict

from src.analysis import build_analysis
from src.data_cleaning import clean_customers, load_raw
from src.download_data import DATA_PATH, DATASET_SHA256, download_dataset


ROOT = Path(__file__).resolve().parents[1]


def run(source: Path = DATA_PATH) -> Dict[str, object]:
    """Execute the full analysis and write reproducible local outputs."""
    source = source if source.is_absolute() else ROOT / source
    if not source.exists():
        download_dataset(source)
    source_hash = sha256(source.read_bytes()).hexdigest()
    if source_hash != DATASET_SHA256:
        raise ValueError("Source file does not match the pinned IBM dataset checksum.")
    raw = load_raw(source)
    cleaned, audit = clean_customers(raw)

    data_dir = ROOT / "data/processed"
    tables_dir = ROOT / "outputs/tables"
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(data_dir / "customers_clean.csv", index=False)
    summary = build_analysis(cleaned, tables_dir)
    audit["source_sha256"] = source_hash
    audit["source_file"] = source.name
    (tables_dir / "data_quality_report.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {"data_quality": audit, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DATA_PATH, help="Path to source CSV (downloaded if absent)")
    args = parser.parse_args()
    print(json.dumps(run(args.source), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
