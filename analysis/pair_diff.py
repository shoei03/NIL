#!/usr/bin/env python3
"""
Pair Difference Analyzer

This module analyzes similar method pairs from snapshot CSV files and computes
the differences (added, deleted, persisted) between adjacent snapshots.
"""

import argparse
import csv
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple

from tqdm import tqdm


# Type alias for a normalized pair key (tuple of two method strings)
PairKey = Tuple[str, str]


class PairDiffAnalyzer:
    """Analyzes differences in method pairs between adjacent snapshots."""

    def __init__(self, log_dir: Path = None):
        """Initialize the analyzer with optional log directory."""
        # Setup log file path
        if log_dir is None:
            log_dir = Path("/app/logs")
        
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pair_diff_{timestamp}.log"

        self.log_file = log_file

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Clear existing handlers to prevent duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()

        self.logger.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Add handlers
        for handler in [
            logging.FileHandler(log_file, mode="a", encoding="utf-8"),
            logging.StreamHandler()
        ]:
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def collect_and_sort_snapshots(self, input_dir: Path) -> list[Path]:
        """
        Collect clone_pairs.csv files and sort by timestamp in filename.
        Directory format: YYYYMMDD_HHMMSS_<commit_hash>
        """
        csv_files: list[Path] = [
            f / "clone_pairs.csv" for f in input_dir.iterdir() if f.is_dir()
        ]

        if not csv_files:
            self.logger.warning(f"No clone_pairs.csv files found in {input_dir}")
            return []

        # Sort by directory name (lexicographic order works for YYYYMMDD_HHMMSS format)
        sorted_files = sorted(csv_files, key=lambda f: f.parent.name)

        self.logger.info(f"Found {len(sorted_files)} snapshot files")
        return sorted_files

    def parse_snapshot(self, csv_path: Path) -> Set[PairKey]:
        """
        Parse a snapshot CSV file and return a set of normalized pair keys.

        Each CSV row has 4 columns (no header):
        method_a, method_b, ngram_similarity, lcs_similarity

        Pair key = tuple(sorted([method_a, method_b])) for undirected pairs
        """
        pairs = set()
        error_count = 0

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for line_num, row in enumerate(reader, 1):
                    if len(row) != 4:
                        # Warn only for non-empty rows
                        if row and any(cell.strip() for cell in row):
                            error_count += 1
                            self.logger.warning(
                                f"{csv_path.name}:{line_num}: Expected 4 columns, got {len(row)}"
                            )
                        continue

                    pairs.add(tuple(sorted([row[0], row[1]])))

            if error_count > 0:
                self.logger.warning(
                    f"{csv_path.name}: Parsed with {error_count} errors, "
                    f"{len(pairs)} unique pairs extracted"
                )
            else:
                self.logger.info(
                    f"{csv_path.parent.name}: {len(pairs)} unique pairs extracted"
                )

            return pairs

        except Exception as e:
            self.logger.error(f"Failed to read {csv_path}: {str(e)}")
            raise

    def write_pair_list(self, pairs: Set[PairKey], output_path: Path) -> None:
        """
        Write a set of pairs to a CSV file.
        Columns: method_a, method_b
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["method_a", "method_b"])
            writer.writerows(sorted(pairs))

    def analyze_snapshots(
        self, input_dir: Path, output_dir: Path, emit_lists: bool = False
    ) -> None:
        """
        Analyze all snapshots in the input directory and compute differences
        between adjacent snapshots.
        """
        snapshot_files = self.collect_and_sort_snapshots(input_dir)

        if len(snapshot_files) < 2:
            self.logger.warning("Need at least 2 snapshot files to compute differences")
            return

        # Open summary CSV file
        summary_path = output_dir / "pair_diff_summary.csv"
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        with open(summary_path, "w", newline="", encoding="utf-8") as summary_file:
            summary_writer = csv.writer(summary_file)
            summary_writer.writerow([
                "snapshot_t", "snapshot_t1", "added_count", "deleted_count",
                "persisted_count", "total", "added_rate", "deleted_rate", "persisted_rate"
            ])

            # Process adjacent pairs of snapshots
            for prev_file, curr_file in tqdm(
                zip(snapshot_files, snapshot_files[1:]),
                desc="Processing snapshots",
                total=len(snapshot_files) - 1
            ):
                prev_set = self.parse_snapshot(prev_file)
                curr_set = self.parse_snapshot(curr_file)

                # Compute differences
                added = curr_set - prev_set
                deleted = prev_set - curr_set
                persisted = prev_set & curr_set

                # Calculate counts and rates
                added_count = len(added)
                deleted_count = len(deleted)
                persisted_count = len(persisted)
                total = added_count + deleted_count + persisted_count

                added_rate = round(added_count / total, 4) if total > 0 else 0.0
                deleted_rate = round(deleted_count / total, 4) if total > 0 else 0.0
                persisted_rate = round(persisted_count / total, 4) if total > 0 else 0.0

                # Write summary row
                summary_writer.writerow([
                    prev_file.parent.name, curr_file.parent.name,
                    added_count, deleted_count, persisted_count, total,
                    added_rate, deleted_rate, persisted_rate
                ])

                self.logger.info(
                    f"{prev_file.parent.name} -> {curr_file.parent.name}: "
                    f"added={added_count}, deleted={deleted_count}, persisted={persisted_count}, "
                    f"total={total}, added_rate={added_rate:.4f}, "
                    f"deleted_rate={deleted_rate:.4f}, persisted_rate={persisted_rate:.4f}"
                )

                # Optionally write detailed lists
                if emit_lists:
                    transition_dir = output_dir / f"{prev_file.parent.name}_to_{curr_file.parent.name}"
                    self.write_pair_list(added, transition_dir / "added.csv")
                    self.write_pair_list(deleted, transition_dir / "deleted.csv")
                    self.write_pair_list(persisted, transition_dir / "persisted.csv")
                    self.logger.info(f"  Detailed lists written to {transition_dir}")

        self.logger.info(f"Summary written to {summary_path}")
        self.logger.info("Analysis complete!")


def main() -> None:
    """Main function to run the pair difference analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze differences in method pairs between adjacent snapshots"
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("/workspace/results"),
        help="Input directory containing snapshot CSV files (default: /workspace/results)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("/app/output/pair_diff_with_lists"),
        help="Output directory for results (default: /app/output/pair_diff_with_lists)",
    )
    parser.add_argument(
        "--emit-lists",
        action="store_true",
        default=True,
        help="Emit detailed CSV lists of added/deleted/persisted pairs (default: True)",
    )
    parser.add_argument(
        "--no-emit-lists",
        action="store_false",
        dest="emit_lists",
        help="Disable emitting detailed CSV lists",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("/app/logs"),
        help="Log directory path (default: /app/logs)",
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory does not exist: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = None
    try:
        # Create analyzer and run analysis
        analyzer = PairDiffAnalyzer(log_dir=args.log_dir)
        analyzer.analyze_snapshots(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            emit_lists=args.emit_lists
        )

    except KeyboardInterrupt:
        msg = "\nAnalysis interrupted by user"
        if analyzer:
            analyzer.logger.warning(msg)
        print(msg, file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        msg = f"Error: {e}"
        if analyzer:
            analyzer.logger.error(msg, exc_info=True)
        else:
            print(msg, file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()