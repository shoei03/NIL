#!/usr/bin/env python3
"""
results/*/ を走査し、analysis/output/results_index.json を生成するスクリプト。

Requirements:
    - Python 3.14+
    - pathlib, logging, tqdm
    
Directory Format:
    YYYYMMDD_HHMMSS_<hash>
    
Output:
    JSON index file containing metadata for all CSV files in result directories
"""

import json
import logging
import re
import sys
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from tqdm import tqdm
from utils.logging_utils import setup_logging

# Type Definitions
class FileInfo(TypedDict):
    """CSV file metadata."""
    path: str
    size_bytes: int


class RunInfo(TypedDict):
    """Run directory metadata."""
    run_id: str
    datetime: str
    hash: str
    dir: str
    files: dict[str, FileInfo]
    file_count: int
    total_size_bytes: int


class IndexData(TypedDict):
    """Complete index structure."""
    generated_at: str
    root: str
    runs: list[RunInfo]
    summary: dict[str, int | str]


# Constants
RESULTS_DIR_CANDIDATES: list[Path] = [
    Path(__file__).parents[1] / "results",
]
OUTPUT_INDEX_PATH: Path = Path(__file__).parent / "output" / "results_index.json"
LOG_PATH: Path = Path(__file__).parent / "logs" / "results_index.log"
RUN_DIR_PATTERN: re.Pattern[str] = re.compile(
    r"^(?P<dt>\d{8}_\d{6})_(?P<hash>[0-9a-fA-F]+)$"
)


def _detect_results_dir() -> Path:
    """
    Detect the results directory from predefined candidates.
    
    Returns:
        Path to the detected results directory.
        
    Raises:
        FileNotFoundError: If no valid results directory is found.
    """
    for candidate in RESULTS_DIR_CANDIDATES:
        if candidate.exists() and candidate.is_dir():
            logging.info("Detected results directory: %s", candidate)
            return candidate
    
    candidates_str = ", ".join(str(c) for c in RESULTS_DIR_CANDIDATES)
    raise FileNotFoundError(
        f"No results directory found. Candidates: {candidates_str}"
    )


def _iter_run_dirs(results_root: Path) -> Iterator[Path]:
    """
    Iterate over run directories matching the expected pattern.
    
    Args:
        results_root: Path to the results directory.
        
    Yields:
        Path objects for valid run directories.
    """
    try:
        for item in sorted(results_root.iterdir()):
            if item.is_dir() and RUN_DIR_PATTERN.match(item.name):
                yield item
    except OSError as e:
        logging.error("Failed to iterate directory: %s - %s", results_root, e)


def _parse_run_metadata(run_dir: Path) -> tuple[datetime, str] | None:
    """
    Extract metadata from run directory name.
    
    Args:
        run_dir: Path to the run directory.
        
    Returns:
        Tuple of (datetime, commit_hash) or None if parsing fails.
    """
    m = RUN_DIR_PATTERN.match(run_dir.name)
    if not m:
        return None
    
    try:
        dt_raw = m.group("dt")
        commit_hash = m.group("hash")
        dt = datetime.strptime(dt_raw, "%Y%m%d_%H%M%S").replace(
            tzinfo=timezone.utc
        )
        return dt, commit_hash
    except (ValueError, KeyError) as e:
        logging.warning("Failed to parse metadata: %s - %s", run_dir.name, e)
        return None


def _collect_csv_files(run_dir: Path) -> dict[str, FileInfo]:
    """
    Collect all CSV files in a run directory.
    
    Args:
        run_dir: Path to the run directory.
        
    Returns:
        Dictionary mapping filename to FileInfo.
    """
    files: dict[str, FileInfo] = {}
    
    try:
        for csv_file in run_dir.glob("*.csv"):
            if not csv_file.is_file():
                continue
            
            try:
                size = csv_file.stat().st_size
                rel_path = Path("results") / run_dir.name / csv_file.name
                files[csv_file.name] = {
                    "path": str(rel_path),
                    "size_bytes": size,
                }
            except OSError as e:
                logging.warning(
                    "Failed to get file info: %s - %s", csv_file, e
                )
    except OSError as e:
        logging.error("Failed to scan CSV files: %s - %s", run_dir, e)
    
    return files


def _process_run_dir(run_dir: Path) -> RunInfo | None:
    """
    Process a single run directory.
    
    Args:
        run_dir: Path to the run directory.
        
    Returns:
        RunInfo object or None if processing fails.
    """
    metadata = _parse_run_metadata(run_dir)
    if metadata is None:
        return None
    
    dt, commit_hash = metadata
    files = _collect_csv_files(run_dir)
    
    if not files:
        logging.warning("No CSV files found: %s", run_dir.name)
    
    total_size = sum(f["size_bytes"] for f in files.values())
    
    return {
        "run_id": run_dir.name,
        "datetime": dt.isoformat(),
        "hash": commit_hash,
        "dir": str(Path("results") / run_dir.name),
        "files": files,
        "file_count": len(files),
        "total_size_bytes": total_size,
    }


def _scan(results_root: Path) -> IndexData:
    """
    Scan the results directory and generate index data.
    
    Args:
        results_root: Path to the results directory.
        
    Returns:
        Complete index data structure.
    """
    runs: list[RunInfo] = []
    error_count = 0
    
    run_dirs = list(_iter_run_dirs(results_root))
    logging.info("Found %d run directories", len(run_dirs))
    
    for run_dir in tqdm(run_dirs, desc="Scanning runs", unit="run"):
        try:
            run_info = _process_run_dir(run_dir)
            if run_info is not None:
                runs.append(run_info)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error processing run: %s - %s", run_dir.name, e, exc_info=True)
            error_count += 1
    
    total_files = sum(r["file_count"] for r in runs)
    total_size = sum(r["total_size_bytes"] for r in runs)
    
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root": "results",
        "runs": runs,
        "summary": {
            "total_runs": len(runs),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "error_count": error_count,
        },
    }


def _validate_index(data: IndexData) -> bool:
    """
    Validate the integrity of generated index data.
    
    Args:
        data: Index data to validate.
        
    Returns:
        True if validation passes, False otherwise.
    """
    try:
        assert "generated_at" in data
        assert "runs" in data
        assert isinstance(data["runs"], list)
        
        for run in data["runs"]:
            assert "run_id" in run
            assert "datetime" in run
            assert "files" in run
            datetime.fromisoformat(run["datetime"].replace("Z", "+00:00"))
        
        logging.info("Index validation: OK")
        return True
    except (AssertionError, ValueError, KeyError) as e:
        logging.error("Index validation failed: %s", e)
        return False


def main() -> int:
    """
    Main execution flow.
    
    Returns:
        Exit code (0: success, 1: failure).
    """
    try:
        setup_logging(LOG_PATH)
        logging.info("=" * 60)
        logging.info("Starting results index generation")
        
        results_root = _detect_results_dir()
        logging.info("Results directory: %s", results_root)
        
        data = _scan(results_root)
        
        if not _validate_index(data):
            logging.error("Index validation failed")
            return 1
        
        OUTPUT_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_INDEX_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        summary = data["summary"]
        logging.info("=" * 60)
        logging.info("Index generation completed")
        logging.info("  Output: %s", OUTPUT_INDEX_PATH)
        logging.info("  Runs: %d", summary["total_runs"])
        logging.info("  Files: %d", summary["total_files"])
        logging.info("  Total size: %.2f MB", summary["total_size_bytes"] / 1024 / 1024)
        if summary["error_count"] > 0:
            logging.warning("  Errors: %d", summary["error_count"])
        logging.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logging.error("File not found: %s", e)
        return 1
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Unexpected error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())