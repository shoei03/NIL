#!/usr/bin/env python3
"""
Pair Difference Analyzer

This module analyzes similar method pairs from snapshot CSV files and computes
the differences (added, deleted, persisted) between adjacent snapshots.
"""

import argparse
import csv
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple

from tqdm import tqdm


@dataclass(frozen=True, order=True)
class MethodID:
    """Represents a method identifier (path, method, args, ret)."""

    path: str
    method: str
    args: str
    ret: str

    def __str__(self) -> str:
        return f"{self.path}:{self.method}:{self.args}:{self.ret}"


# Type alias for a normalized pair key
PairKey = Tuple[MethodID, MethodID]


class PairDiffAnalyzer:
    """Analyzes differences in method pairs between adjacent snapshots."""

    def __init__(self, log_file: Path = None):
        """Initialize the analyzer with optional log file."""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"pair_diff_{timestamp}.log"

        # Create file handler
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.log_file = log_file

    def extract_timestamp_from_filename(self, filename: str) -> Tuple[str, str] | None:
        """
        Extract timestamp from filename pattern: results_YYYYMMDD_HHMMSS_*.csv
        Returns (date_str, time_str) or None if pattern doesn't match.
        """
        match = re.search(r"results_(\d{8})_(\d{6})_", filename)
        if match:
            return match.group(1), match.group(2)
        return None

    def collect_and_sort_snapshots(self, input_dir: Path) -> List[Path]:
        """
        Collect results_*.csv files and sort by timestamp in filename.
        Files without valid timestamps are placed at the end.
        """
        csv_files = list(input_dir.glob("results_*.csv"))

        if not csv_files:
            self.logger.warning(f"No results_*.csv files found in {input_dir}")
            return []

        # Separate files with and without valid timestamps
        files_with_ts = []
        files_without_ts = []

        for file_path in csv_files:
            ts = self.extract_timestamp_from_filename(file_path.name)
            if ts:
                date_str, time_str = ts
                # Create sortable key: YYYYMMDDHHMMSS
                sort_key = date_str + time_str
                files_with_ts.append((sort_key, file_path))
            else:
                files_without_ts.append(file_path)

        # Sort files with timestamps
        files_with_ts.sort(key=lambda x: x[0])
        sorted_files = [path for _, path in files_with_ts] + files_without_ts

        self.logger.info(f"Found {len(sorted_files)} snapshot files")
        return sorted_files

    def parse_snapshot(self, csv_path: Path) -> Set[PairKey]:
        """
        Parse a snapshot CSV file and return a set of normalized pair keys.

        Each CSV row has 12 columns (no header):
        path_a, start_a, end_a, method_a, ret_a, args_a,
        path_b, start_b, end_b, method_b, ret_b, args_b

        Method ID = (path, method, args, ret) - ignoring start/end
        Pair key = tuple(sorted([M_a, M_b])) for undirected pairs
        """
        pairs = set()
        error_count = 0

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for line_num, row in enumerate(reader, 1):
                    # Skip empty lines
                    if not row or all(cell.strip() == "" for cell in row):
                        continue

                    # Check column count
                    if len(row) != 12:
                        error_count += 1
                        self.logger.warning(
                            f"{csv_path.name}:{line_num}: Expected 12 columns, got {len(row)}"
                        )
                        continue

                    try:
                        # Extract columns
                        (
                            path_a,
                            start_a,
                            end_a,
                            method_a,
                            ret_a,
                            args_a,
                            path_b,
                            start_b,
                            end_b,
                            method_b,
                            ret_b,
                            args_b,
                        ) = row

                        # Create Method IDs (ignoring start/end, trimming whitespace)
                        m_a = MethodID(
                            path=path_a.strip(),
                            method=method_a.strip(),
                            args=args_a.strip(),
                            ret=ret_a.strip(),
                        )

                        m_b = MethodID(
                            path=path_b.strip(),
                            method=method_b.strip(),
                            args=args_b.strip(),
                            ret=ret_b.strip(),
                        )

                        # Create normalized pair key (undirected)
                        pair_key = tuple(sorted([m_a, m_b]))
                        pairs.add(pair_key)

                    except Exception as e:
                        error_count += 1
                        self.logger.warning(
                            f"{csv_path.name}:{line_num}: Error parsing row - {str(e)}"
                        )
                        continue

        except Exception as e:
            self.logger.error(f"Failed to read {csv_path}: {str(e)}")
            raise

        if error_count > 0:
            self.logger.warning(
                f"{csv_path.name}: Parsed with {error_count} errors, "
                f"{len(pairs)} unique pairs extracted"
            )
        else:
            self.logger.info(f"{csv_path.name}: {len(pairs)} unique pairs extracted")

        return pairs

    def write_pair_list(self, pairs: Set[PairKey], output_path: Path) -> None:
        """
        Write a set of pairs to a CSV file.
        Columns: A_path, A_method, A_args, A_ret, B_path, B_method, B_args, B_ret
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(
                [
                    "A_path",
                    "A_method",
                    "A_args",
                    "A_ret",
                    "B_path",
                    "B_method",
                    "B_args",
                    "B_ret",
                ]
            )

            # Write pairs (sorted for deterministic output)
            for m_a, m_b in sorted(pairs):
                writer.writerow(
                    [
                        m_a.path,
                        m_a.method,
                        m_a.args,
                        m_a.ret,
                        m_b.path,
                        m_b.method,
                        m_b.args,
                        m_b.ret,
                    ]
                )

    def analyze_snapshots(
        self, input_dir: Path, output_dir: Path, emit_lists: bool = False
    ) -> None:
        """
        Analyze all snapshots in the input directory and compute differences
        between adjacent snapshots.
        """
        # Collect and sort snapshot files
        snapshot_files = self.collect_and_sort_snapshots(input_dir)

        if len(snapshot_files) < 2:
            self.logger.warning("Need at least 2 snapshot files to compute differences")
            return

        # Prepare output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Open summary CSV file
        summary_path = output_dir / "pair_diff_summary.csv"
        with open(summary_path, "w", newline="", encoding="utf-8") as summary_file:
            summary_writer = csv.writer(summary_file)
            summary_writer.writerow(
                ["t_file", "t1_file", "added_count", "deleted_count", "persisted_count"]
            )

            # Process adjacent pairs of snapshots
            prev_set = None
            prev_file = None

            for i, curr_file in enumerate(
                tqdm(snapshot_files, desc="Processing snapshots")
            ):
                # Parse current snapshot
                curr_set = self.parse_snapshot(curr_file)

                # Compare with previous snapshot if available
                if prev_set is not None:
                    # Compute differences
                    added = curr_set - prev_set
                    deleted = prev_set - curr_set
                    persisted = prev_set & curr_set

                    # Write summary row
                    summary_writer.writerow(
                        [
                            prev_file.name,
                            curr_file.name,
                            len(added),
                            len(deleted),
                            len(persisted),
                        ]
                    )

                    self.logger.info(
                        f"{prev_file.name} -> {curr_file.name}: "
                        f"added={len(added)}, deleted={len(deleted)}, persisted={len(persisted)}"
                    )

                    # Optionally write detailed lists
                    if emit_lists:
                        # Create subdirectory for this transition
                        prev_basename = prev_file.stem
                        curr_basename = curr_file.stem
                        transition_dir = (
                            output_dir / f"{prev_basename}_to_{curr_basename}"
                        )

                        self.write_pair_list(added, transition_dir / "added.csv")
                        self.write_pair_list(deleted, transition_dir / "deleted.csv")
                        self.write_pair_list(
                            persisted, transition_dir / "persisted.csv"
                        )

                        self.logger.info(
                            f"  Detailed lists written to {transition_dir}"
                        )

                # Move to next iteration
                prev_set = curr_set
                prev_file = curr_file

        self.logger.info(f"Summary written to {summary_path}")
        self.logger.info("Analysis complete!")


def main():
    """Main function to run the pair difference analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze differences in method pairs between adjacent snapshots"
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=str,
        required=True,
        help="Input directory containing snapshot CSV files",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for results",
    )
    parser.add_argument(
        "--emit-lists",
        action="store_true",
        help="Emit detailed CSV lists of added/deleted/persisted pairs",
    )
    parser.add_argument(
        "--log",
        type=str,
        help="Log file path (default: logs/pair_diff_TIMESTAMP.log)",
    )

    args = parser.parse_args()

    # Setup paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    log_path = Path(args.log) if args.log else None

    # Ensure log directory exists
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Validate input directory
        if not input_dir.exists():
            print(
                f"Error: Input directory does not exist: {input_dir}", file=sys.stderr
            )
            sys.exit(1)

        # Create analyzer
        analyzer = PairDiffAnalyzer(log_file=log_path)

        # Run analysis
        analyzer.analyze_snapshots(
            input_dir=input_dir, output_dir=output_dir, emit_lists=args.emit_lists
        )

    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
