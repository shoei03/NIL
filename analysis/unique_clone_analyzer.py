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
    """Represents a code block with file path, line range, function name, return type, and parameters."""

    file_path: str
    start_line: int
    end_line: int
    function_name: str
    return_type: str
    parameters: str

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
        return f"{self.file_path}:{self.start_line}-{self.end_line}:{self.function_name}:{self.return_type}:{self.parameters}"


@dataclass(frozen=True)
class CodeClonePair:
    """Represents a pair of code blocks that are clones of each other."""

    block1: CodeBlock
    block2: CodeBlock

    def __post_init__(self):
        """Normalize the pair to ensure consistent ordering."""
        # Create a normalized version where blocks are ordered consistently
        if (
            self.block1.file_path,
            self.block1.start_line,
            self.block1.end_line,
            self.block1.function_name,
            self.block1.return_type,
            self.block1.parameters,
        ) > (
            self.block2.file_path,
            self.block2.start_line,
            self.block2.end_line,
            self.block2.function_name,
            self.block2.return_type,
            self.block2.parameters,
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
        self.logger.setLevel(logging.INFO)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create logs directory
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"clone_analyzer_{timestamp}.log"

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

    def parse_csv_line(self, row: List[str]) -> CodeClonePair:
        """Parse a CSV row into a CodeClonePair."""
        # Skip already processed files (15 columns: 12 original + 3 new)
        if len(row) == 15:
            return None
        elif len(row) != 12:
            raise ValueError(f"Expected 12 columns, got {len(row)}: {row}")

        try:
            (
                file1,
                start1,
                end1,
                func1,
                return1,
                params1,
                file2,
                start2,
                end2,
                func2,
                return2,
                params2,
            ) = row

            block1 = CodeBlock(
                file_path=file1.strip(),
                start_line=int(start1.strip()),
                end_line=int(end1.strip()),
                function_name=func1.strip(),
                return_type=return1.strip(),
                parameters=params1.strip(),
            )

            block2 = CodeBlock(
                file_path=file2.strip(),
                start_line=int(start2.strip()),
                end_line=int(end2.strip()),
                function_name=func2.strip(),
                return_type=return2.strip(),
                parameters=params2.strip(),
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

    def split_csv_line(self, line: str) -> List[str]:
        """Split a CSV line, ignoring commas inside square brackets."""
        result = []
        current = []
        bracket_depth = 0

        for char in line:
            if char == "[":
                bracket_depth += 1
                current.append(char)
            elif char == "]":
                bracket_depth -= 1
                current.append(char)
            elif char == "," and bracket_depth == 0:
                # This comma is a column separator
                result.append("".join(current))
                current = []
            else:
                current.append(char)

        # Add the last field
        if current:
            result.append("".join(current))

        return result

    def analyze_csv_file(self, csv_file_path: Path) -> None:
        """Analyze a CSV file containing code clone pairs."""
        if not csv_file_path.exists():
            error_msg = f"CSV file not found: {csv_file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        error_count = 0
        with open(csv_file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue  # Skip empty lines

                    # Use custom CSV parser that respects brackets
                    row = self.split_csv_line(line)

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
                        "file1",
                        "start1",
                        "end1",
                        "function1",
                        "return_type1",
                        "parameters1",
                        "file2",
                        "start2",
                        "end2",
                        "function2",
                        "return_type2",
                        "parameters2",
                        "pair_id",
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
                            pair.block1.file_path,
                            pair.block1.start_line,
                            pair.block1.end_line,
                            pair.block1.function_name,
                            pair.block1.return_type,
                            pair.block1.parameters,
                            pair.block2.file_path,
                            pair.block2.start_line,
                            pair.block2.end_line,
                            pair.block2.function_name,
                            pair.block2.return_type,
                            pair.block2.parameters,
                            pair_id,
                            is_first,
                            pair.get_hash(),
                        ]
                    )
        except Exception as e:
            error_msg = f"Failed to save results to {output_path}: {str(e)}"
            self.logger.error(error_msg)
            raise IOError(error_msg)


def process_all_results_files(
    input_dir: Path, output_dir: Path = None, log_file: Path = None
) -> None:
    """Process all CSV files in the input directory."""
    # Setup logging for this function
    logger = logging.getLogger("process_all_results_files")
    logger.setLevel(logging.INFO)

    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # If output_dir is not specified, overwrite input files
    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Find all CSV files in the input directory
    csv_files = sorted(input_dir.glob("*.csv"))

    if not csv_files:
        logger.warning(f"No CSV files found in {input_dir}")
        return

    logger.info(f"Found {len(csv_files)} CSV files to process in {input_dir}")
    if output_dir != input_dir:
        logger.info(f"Output directory: {output_dir}")

    # Process each CSV file
    for csv_file in tqdm(csv_files, desc="Processing CSV files"):
        try:
            # Create analyzer for this file
            analyzer = UniqueCloneAnalyzer(log_file=log_file)

            # Analyze the CSV file
            analyzer.analyze_csv_file(csv_file)

            # Determine output path
            output_path = output_dir / csv_file.name

            # Save results
            analyzer.save_results(output_path)

        except Exception as e:
            logger.error(f"Failed to process {csv_file.name}: {str(e)}")
            continue

    logger.info("\nAll files processed successfully!")


def main():
    """Main function to run the analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze unique code clone pairs from CSV files"
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=str,
        help="Input directory containing CSV files (default: ../results)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        help="Output directory for processed CSV files (default: same as input_dir)",
    )
    parser.add_argument(
        "-l",
        "--log",
        type=str,
        default="logs/clone_analyzer.log",
        help="Log file path (default: logs/clone_analyzer.log)",
    )

    args = parser.parse_args()

    log_path = Path(args.log) if args.log else None

    # Ensure log directory exists
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Determine input directory
        if args.input_dir:
            input_dir = Path(args.input_dir)
        else:
            # Default to ../results from the script location
            script_dir = Path(__file__).parent
            input_dir = script_dir.parent / "results"

        # Determine output directory
        output_dir = Path(args.output_dir) if args.output_dir else None

        process_all_results_files(
            input_dir=input_dir, output_dir=output_dir, log_file=log_path
        )

    except Exception as e:
        raise SystemExit(f"Error: {e}")


if __name__ == "__main__":
    main()
