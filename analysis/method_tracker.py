#!/usr/bin/env python3
"""
Method Evolution Tracker

Tracks methods across snapshots using exact matching (path, method name, signature).
This is the basic implementation for Phase 1.
"""

import argparse
import csv
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm


@dataclass(frozen=True)
class MethodInfo:
    """Represents a method with its metadata."""

    file_path: str
    start_line: int
    end_line: int
    method_name: str
    return_type: str
    parameters: str
    commit_hash: str
    token_hash: str

    @property
    def signature(self) -> str:
        """Get method signature (name + parameters + return_type)."""
        return f"{self.method_name}:{self.parameters}:{self.return_type}"

    @property
    def full_id(self) -> str:
        """Get full method ID (path + signature)."""
        return f"{self.file_path}::{self.signature}"

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}:{self.method_name}"


@dataclass
class MethodMatch:
    """Represents a match between two methods across snapshots."""

    method_t: MethodInfo
    method_t1: MethodInfo
    match_type: str
    similarity: float = 1.0


class MethodTracker:
    """Tracks methods across snapshots."""

    def __init__(self, log_file: Optional[Path] = None):
        """Initialize the tracker with optional log file."""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"method_tracker_{timestamp}.log"

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

    def parse_code_blocks(self, file_path: Path) -> Dict[str, MethodInfo]:
        """
        Parse code_blocks file and return a dictionary of methods.

        Expected format (8 columns):
        file,start,end,method,return_type,[params],commit_hash,token_hash
        """
        methods = {}
        error_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        parts = line.split(",")

                        # Check if this is the new format with 8 columns
                        if len(parts) >= 8:
                            file_p = parts[0]
                            start = int(parts[1])
                            end = int(parts[2])
                            method = parts[3]
                            ret_type = parts[4]
                            # Handle parameters in brackets
                            params_match = re.search(r"\[(.*?)\]", line)
                            params = params_match.group(1) if params_match else ""
                            commit_hash = parts[-2]
                            token_hash = parts[-1]

                            method_info = MethodInfo(
                                file_path=file_p,
                                start_line=start,
                                end_line=end,
                                method_name=method,
                                return_type=ret_type,
                                parameters=params,
                                commit_hash=commit_hash,
                                token_hash=token_hash,
                            )

                            methods[method_info.full_id] = method_info

                        elif len(parts) == 3:
                            # Old format without method info, skip
                            continue
                        else:
                            error_count += 1
                            self.logger.warning(
                                f"{file_path.name}:{line_num}: Unexpected format ({len(parts)} columns)"
                            )

                    except Exception as e:
                        error_count += 1
                        self.logger.warning(
                            f"{file_path.name}:{line_num}: Error parsing line - {str(e)}"
                        )

        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {str(e)}")
            raise

        if error_count > 0:
            self.logger.warning(
                f"{file_path.name}: Parsed with {error_count} errors, "
                f"{len(methods)} methods extracted"
            )
        else:
            self.logger.info(f"{file_path.name}: {len(methods)} methods extracted")

        return methods

    def find_exact_matches(
        self,
        snapshot_t: Dict[str, MethodInfo],
        snapshot_t1: Dict[str, MethodInfo],
    ) -> List[MethodMatch]:
        """
        Find exact matches between two snapshots.

        Match criteria:
        - Same file path
        - Same method name
        - Same signature (parameters + return type)
        """
        matches = []

        for full_id, method_info in snapshot_t.items():
            if full_id in snapshot_t1:
                matches.append(
                    MethodMatch(
                        method_t=method_info,
                        method_t1=snapshot_t1[full_id],
                        match_type="exact",
                        similarity=1.0,
                    )
                )

        return matches

    def analyze_changes(
        self,
        snapshot_t: Dict[str, MethodInfo],
        snapshot_t1: Dict[str, MethodInfo],
    ) -> Tuple[List[MethodMatch], Set[str], Set[str]]:
        """
        Analyze changes between two snapshots.

        Returns:
            (matches, added_ids, deleted_ids)
        """
        # Find exact matches
        matches = self.find_exact_matches(snapshot_t, snapshot_t1)

        # Get matched method IDs
        matched_t = {match.method_t.full_id for match in matches}
        matched_t1 = {match.method_t1.full_id for match in matches}

        # Find added and deleted methods
        added_ids = set(snapshot_t1.keys()) - matched_t1
        deleted_ids = set(snapshot_t.keys()) - matched_t

        return matches, added_ids, deleted_ids

    def track_methods(self, code_blocks_dir: Path, output_dir: Path) -> None:
        """
        Track methods across all code_blocks files in the directory.

        Assumes files are named: code_blocks_<commit_hash>
        Or in code_blocks subdirectory: code_blocks/code_blocks_<commit_hash>
        """
        # Check if code_blocks_dir has a code_blocks subdirectory
        code_blocks_subdir = code_blocks_dir / "code_blocks"
        if code_blocks_subdir.exists() and code_blocks_subdir.is_dir():
            search_dir = code_blocks_subdir
            self.logger.info(f"Using code_blocks subdirectory: {search_dir}")
        else:
            search_dir = code_blocks_dir
            self.logger.info(f"Using directory: {search_dir}")

        # Find all code_blocks files
        code_block_files = sorted(search_dir.glob("code_blocks_*"))

        if len(code_block_files) < 2:
            self.logger.warning(
                f"Need at least 2 code_blocks files to track methods (found {len(code_block_files)} in {search_dir})"
            )
            return

        self.logger.info(f"Found {len(code_block_files)} code_blocks files")

        # Prepare output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Open output files
        summary_path = output_dir / "method_tracking_summary.csv"
        details_path = output_dir / "method_tracking_details.csv"

        with (
            open(summary_path, "w", newline="", encoding="utf-8") as summary_f,
            open(details_path, "w", newline="", encoding="utf-8") as details_f,
        ):
            summary_writer = csv.writer(summary_f)
            details_writer = csv.writer(details_f)

            # Write headers
            summary_writer.writerow(
                [
                    "snapshot_t",
                    "snapshot_t1",
                    "exact_matches",
                    "added_methods",
                    "deleted_methods",
                    "total_t",
                    "total_t1",
                ]
            )

            details_writer.writerow(
                [
                    "snapshot_t",
                    "snapshot_t1",
                    "change_type",
                    "file_path",
                    "method_name",
                    "signature",
                    "line_range_t",
                    "line_range_t1",
                    "commit_t",
                    "commit_t1",
                ]
            )

            # Process adjacent pairs
            prev_file = None
            prev_snapshot = None

            for curr_file in tqdm(code_block_files, desc="Tracking methods"):
                # Parse current snapshot
                curr_snapshot = self.parse_code_blocks(curr_file)
                curr_commit = curr_file.name.replace("code_blocks_", "")

                if prev_snapshot is not None:
                    prev_commit = prev_file.name.replace("code_blocks_", "")

                    # Analyze changes
                    matches, added_ids, deleted_ids = self.analyze_changes(
                        prev_snapshot, curr_snapshot
                    )

                    # Write summary
                    summary_writer.writerow(
                        [
                            prev_commit,
                            curr_commit,
                            len(matches),
                            len(added_ids),
                            len(deleted_ids),
                            len(prev_snapshot),
                            len(curr_snapshot),
                        ]
                    )

                    # Write exact matches
                    for match in matches:
                        details_writer.writerow(
                            [
                                prev_commit,
                                curr_commit,
                                "exact_match",
                                match.method_t.file_path,
                                match.method_t.method_name,
                                match.method_t.signature,
                                f"{match.method_t.start_line}-{match.method_t.end_line}",
                                f"{match.method_t1.start_line}-{match.method_t1.end_line}",
                                match.method_t.commit_hash,
                                match.method_t1.commit_hash,
                            ]
                        )

                    # Write added methods
                    for method_id in added_ids:
                        method = curr_snapshot[method_id]
                        details_writer.writerow(
                            [
                                prev_commit,
                                curr_commit,
                                "added",
                                method.file_path,
                                method.method_name,
                                method.signature,
                                "",
                                f"{method.start_line}-{method.end_line}",
                                "",
                                method.commit_hash,
                            ]
                        )

                    # Write deleted methods
                    for method_id in deleted_ids:
                        method = prev_snapshot[method_id]
                        details_writer.writerow(
                            [
                                prev_commit,
                                curr_commit,
                                "deleted",
                                method.file_path,
                                method.method_name,
                                method.signature,
                                f"{method.start_line}-{method.end_line}",
                                "",
                                method.commit_hash,
                                "",
                            ]
                        )

                    self.logger.info(
                        f"{prev_commit} -> {curr_commit}: "
                        f"exact={len(matches)}, added={len(added_ids)}, deleted={len(deleted_ids)}"
                    )

                prev_file = curr_file
                prev_snapshot = curr_snapshot

        self.logger.info(f"Summary written to {summary_path}")
        self.logger.info(f"Details written to {details_path}")
        self.logger.info("Method tracking complete!")


def main():
    """Main function to run the method tracker."""
    parser = argparse.ArgumentParser(
        description="Track methods across code_blocks snapshots"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Directory containing code_blocks_* files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for tracking results",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="Log file path (optional)",
    )

    args = parser.parse_args()

    # Run tracker
    tracker = MethodTracker(log_file=args.log)
    tracker.logger.info(f"Input directory: {args.input}")
    tracker.logger.info(f"Output directory: {args.output}")
    tracker.logger.info(f"Log file: {tracker.log_file}")

    tracker.track_methods(args.input, args.output)


if __name__ == "__main__":
    main()
