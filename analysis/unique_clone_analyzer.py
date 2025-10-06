#!/usr/bin/env python3
"""
Unique Code Clone Pair Analyzer

This module analyzes code clone pairs from CSV files and assigns unique IDs to each pair.
When a pair appears multiple times, it reuses the same ID to identify unique clone patterns.
"""

import csv
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from tqdm import tqdm


@dataclass(frozen=True)
class CodeBlock:
    """Represents a code block with file path and line range."""

    file_path: str
    start_line: int
    end_line: int

    def __post_init__(self):
        """Validate the code block data."""
        if self.start_line <= 0 or self.end_line <= 0:
            raise ValueError(
                f"Line numbers must be positive: {self.start_line}-{self.end_line}"
            )
        if self.start_line > self.end_line:
            raise ValueError(
                f"Start line must be <= end line: {self.start_line}-{self.end_line}"
            )

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


@dataclass(frozen=True)
class CodeClonePair:
    """Represents a pair of code blocks that are clones of each other."""

    block1: CodeBlock
    block2: CodeBlock

    def __post_init__(self):
        """Normalize the pair to ensure consistent ordering."""
        # Create a normalized version where blocks are ordered consistently
        if (self.block1.file_path, self.block1.start_line, self.block1.end_line) > (
            self.block2.file_path,
            self.block2.start_line,
            self.block2.end_line,
        ):
            # Swap blocks to maintain consistent ordering
            object.__setattr__(self, "block1", self.block2)
            object.__setattr__(self, "block2", self.block1)

    def get_hash(self) -> str:
        """Generate a unique hash for this pair."""
        content = f"{self.block1}|{self.block2}"
        return hashlib.md5(content.encode()).hexdigest()

    def __str__(self) -> str:
        return f"({self.block1}) <-> ({self.block2})"


class UniqueCloneAnalyzer:
    """Analyzes code clone pairs and assigns unique IDs."""

    def __init__(self, log_file: Path = None):
        self.pair_to_id: Dict[str, int] = {}  # hash -> pair_id
        self.next_id: int = 1
        self.processed_pairs: List[
            Tuple[CodeClonePair, int, bool]
        ] = []  # pair, id, is_first

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create logs directory
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"clone_analyzer_errors_{timestamp}.log"

        # Create file handler
        handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        handler.setLevel(logging.ERROR)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(handler)
        self.log_file = log_file

    def parse_csv_line(self, row: List[str]) -> CodeClonePair:
        """Parse a CSV row into a CodeClonePair."""
        # Skip already processed files (9 columns)
        if len(row) == 9:
            return None
        elif len(row) != 6:
            raise ValueError(f"Expected 6 columns, got {len(row)}: {row}")

        try:
            file1, start1, end1, file2, start2, end2 = row

            block1 = CodeBlock(
                file_path=file1.strip(),
                start_line=int(start1.strip()),
                end_line=int(end1.strip()),
            )

            block2 = CodeBlock(
                file_path=file2.strip(),
                start_line=int(start2.strip()),
                end_line=int(end2.strip()),
            )

            return CodeClonePair(block1, block2)

        except ValueError as e:
            raise ValueError(f"Error parsing row {row}: {e}")

    def process_pair(self, pair: CodeClonePair) -> Tuple[int, bool]:
        """Process a code clone pair and return (pair_id, is_first_occurrence)."""
        pair_hash = pair.get_hash()

        if pair_hash in self.pair_to_id:
            # This pair has been seen before
            pair_id = self.pair_to_id[pair_hash]
            is_first = False
        else:
            # This is a new unique pair
            pair_id = self.next_id
            self.pair_to_id[pair_hash] = pair_id
            self.next_id += 1
            is_first = True

        self.processed_pairs.append((pair, pair_id, is_first))
        return pair_id, is_first

    def analyze_csv_file(self, csv_file_path: Path) -> None:
        """Analyze a CSV file containing code clone pairs."""
        if not csv_file_path.exists():
            error_msg = f"CSV file not found: {csv_file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        error_count = 0
        with open(csv_file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)

            for line_num, row in enumerate(reader, 1):
                try:
                    if not row or len(row) == 0:
                        continue  # Skip empty lines

                    pair = self.parse_csv_line(row)
                    if pair is None:
                        continue  # Skip already processed rows

                    self.process_pair(pair)

                except ValueError as e:
                    error_count += 1
                    self.logger.error(
                        f"Line {line_num}: Failed to parse row - {str(e)}"
                    )
                    continue
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Line {line_num}: Unexpected error - {str(e)}")
                    continue

        if error_count > 0:
            self.logger.error(
                f"Analysis completed with {error_count} errors. "
                f"Total pairs processed: {len(self.processed_pairs)}, "
                f"Unique pairs: {len(self.pair_to_id)}"
            )

    def save_results(self, output_path: Path) -> None:
        """Save the analysis results to a CSV file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Write header
                writer.writerow(
                    [
                        "pair_id",
                        "file1",
                        "start1",
                        "end1",
                        "file2",
                        "start2",
                        "end2",
                        "is_first_occurrence",
                        "pair_hash",
                    ]
                )

                # Write data
                for pair, pair_id, is_first in tqdm(
                    self.processed_pairs, desc="Writing results"
                ):
                    writer.writerow(
                        [
                            pair_id,
                            pair.block1.file_path,
                            pair.block1.start_line,
                            pair.block1.end_line,
                            pair.block2.file_path,
                            pair.block2.start_line,
                            pair.block2.end_line,
                            is_first,
                            pair.get_hash(),
                        ]
                    )
        except Exception as e:
            error_msg = f"Failed to save results to {output_path}: {str(e)}"
            self.logger.error(error_msg)
            raise IOError(error_msg)


def process_all_results_files(results_dir: Path = None, log_file: Path = None) -> None:
    """Process all CSV files in the results directory."""
    if results_dir is None:
        # Default to ../results from the script location
        script_dir = Path(__file__).parent
        results_dir = script_dir.parent / "results"

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    # Find all CSV files in the results directory
    csv_files = sorted(results_dir.glob("*.csv"))

    if not csv_files:
        logging.warning(f"No CSV files found in {results_dir}")
        return

    print(f"Found {len(csv_files)} CSV files to process in {results_dir}")

    # Process each CSV file
    for csv_file in tqdm(csv_files, desc="Processing CSV files"):
        try:
            # Create analyzer for this file
            analyzer = UniqueCloneAnalyzer(log_file=log_file)

            # Analyze the CSV file
            analyzer.analyze_csv_file(csv_file)

            # Save results (overwrite original file)
            analyzer.save_results(csv_file)

        except Exception as e:
            logging.error(f"Failed to process {csv_file.name}: {str(e)}")
            continue

    print("\nAll files processed successfully!")


def main():
    """Main function to run the analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze unique code clone pairs from CSV files"
    )
    parser.add_argument(
        "input_csv", type=str, nargs="?", help="Input CSV file path (optional)"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output CSV file path (default: input_with_ids.csv)",
    )
    parser.add_argument(
        "-l",
        "--log",
        type=str,
        help="Log file path (default: logs/clone_analyzer_errors_<timestamp>.log)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Process all CSV files in the results directory",
    )
    parser.add_argument(
        "-r",
        "--results-dir",
        type=str,
        help="Results directory path (default: ../results)",
    )

    args = parser.parse_args()

    log_path = Path(args.log) if args.log else None

    try:
        if args.all:
            # Process all files in results directory
            results_dir = Path(args.results_dir) if args.results_dir else None
            process_all_results_files(results_dir=results_dir, log_file=log_path)
        else:
            # Process single file
            if not args.input_csv:
                parser.error("input_csv is required when not using --all option")

            input_path = Path(args.input_csv)

            if args.output:
                output_path = Path(args.output)
            else:
                # Default: overwrite the original file (same as --all option)
                output_path = input_path

            analyzer = UniqueCloneAnalyzer(log_file=log_path)
            analyzer.analyze_csv_file(input_path)
            analyzer.save_results(output_path)

            print(
                f"Analysis completed: "
                f"Total pairs: {len(analyzer.processed_pairs)}, "
                f"Unique pairs: {len(analyzer.pair_to_id)}"
            )

    except Exception as e:
        raise SystemExit(f"Error: {e}")


if __name__ == "__main__":
    main()
