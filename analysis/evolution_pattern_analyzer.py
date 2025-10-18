#!/usr/bin/env python3
"""
Evolution Pattern Analyzer

Analyzes method evolution patterns across snapshots using method tracking data.
This tool provides insights into:
- Method lifecycle (birth, evolution, death)
- Refactoring patterns
- Code quality trends
- Clone evolution patterns
"""

import argparse
import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class MethodSnapshot:
    """Represents a method at a specific snapshot."""

    snapshot: str
    file_path: str
    method_name: str
    signature: str
    line_range: str
    commit: str
    similarity: float = 1.0


@dataclass
class MethodEvolution:
    """Represents the evolution of a method across snapshots."""

    method_id: str  # Unique identifier
    snapshots: List[MethodSnapshot]
    change_types: List[str]  # History of change types
    birth_snapshot: str
    death_snapshot: str = None

    @property
    def lifespan(self) -> int:
        """Number of snapshots this method existed."""
        return len(self.snapshots)

    @property
    def stability(self) -> float:
        """Stability metric: ratio of exact matches to total transitions."""
        if len(self.change_types) == 0:
            return 1.0
        exact_count = sum(1 for ct in self.change_types if ct == "exact")
        return exact_count / len(self.change_types)

    @property
    def was_renamed(self) -> bool:
        """Check if method was ever renamed."""
        return "renamed" in self.change_types

    @property
    def was_moved(self) -> bool:
        """Check if method was ever moved to different file."""
        return "moved" in self.change_types

    @property
    def was_refactored(self) -> bool:
        """Check if method underwent refactoring."""
        return (
            "refactored" in self.change_types
            or "signature_changed" in self.change_types
        )


class EvolutionPatternAnalyzer:
    """Analyzes method evolution patterns."""

    def __init__(self, log_file: Path = None):
        """Initialize the analyzer."""
        self.logger = self._setup_logging(log_file)
        self.method_evolutions: Dict[str, MethodEvolution] = {}

    def _setup_logging(self, log_file: Path = None) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"evolution_analyzer_{timestamp}.log"

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

        return logger

    def load_tracking_details(self, details_file: Path) -> None:
        """Load method tracking details and build evolution chains."""
        self.logger.info(f"Loading tracking details from {details_file}")

        # Track method instances across snapshots
        method_by_snapshot: Dict[Tuple[str, str], MethodSnapshot] = {}
        transitions: List[
            Tuple[str, str, str, str, float]
        ] = []  # (snap_t, snap_t1, method_t_id, method_t1_id, change_type, similarity)

        with open(details_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                snap_t = row["snapshot_t"]
                snap_t1 = row["snapshot_t1"]
                change_type = row["change_type"]

                if change_type == "added":
                    # New method in t1
                    method_id = f"{row['file_path']}::{row['method_name']}"
                    method_snapshot = MethodSnapshot(
                        snapshot=snap_t1,
                        file_path=row["file_path"],
                        method_name=row["method_name"],
                        signature=row["signature"],
                        line_range=row["line_range_t1"],
                        commit=row["commit_t1"],
                        similarity=1.0,
                    )
                    method_by_snapshot[(snap_t1, method_id)] = method_snapshot

                elif change_type == "deleted":
                    # Method existed in t but not in t1
                    pass

                else:
                    # Match types: exact, token_hash, renamed, moved, signature_changed, refactored
                    method_id_t = f"{row['file_path']}::{row['method_name']}"
                    similarity = float(row["similarity"]) if row["similarity"] else 1.0

                    # Record transition
                    transitions.append(
                        (snap_t, snap_t1, method_id_t, change_type, similarity)
                    )

        self.logger.info(f"Loaded {len(transitions)} method transitions")

        # Build evolution chains
        # TODO: Implement chain building logic

    def analyze_lifecycle_patterns(self) -> Dict[str, any]:
        """Analyze method lifecycle patterns."""
        stats = {
            "total_methods": len(self.method_evolutions),
            "average_lifespan": 0.0,
            "short_lived": 0,  # lifespan <= 2
            "long_lived": 0,  # lifespan >= 10
            "renamed_methods": 0,
            "moved_methods": 0,
            "refactored_methods": 0,
        }

        if not self.method_evolutions:
            return stats

        total_lifespan = 0
        for evolution in self.method_evolutions.values():
            lifespan = evolution.lifespan
            total_lifespan += lifespan

            if lifespan <= 2:
                stats["short_lived"] += 1
            if lifespan >= 10:
                stats["long_lived"] += 1

            if evolution.was_renamed:
                stats["renamed_methods"] += 1
            if evolution.was_moved:
                stats["moved_methods"] += 1
            if evolution.was_refactored:
                stats["refactored_methods"] += 1

        stats["average_lifespan"] = total_lifespan / len(self.method_evolutions)

        return stats

    def analyze_stability_patterns(self) -> Dict[str, any]:
        """Analyze method stability patterns."""
        stability_scores = [e.stability for e in self.method_evolutions.values()]

        if not stability_scores:
            return {}

        return {
            "average_stability": sum(stability_scores) / len(stability_scores),
            "highly_stable": sum(1 for s in stability_scores if s >= 0.9),
            "unstable": sum(1 for s in stability_scores if s < 0.5),
        }

    def generate_report(self, output_dir: Path) -> None:
        """Generate evolution pattern analysis report."""
        output_dir.mkdir(parents=True, exist_ok=True)

        lifecycle_stats = self.analyze_lifecycle_patterns()
        stability_stats = self.analyze_stability_patterns()

        # Write summary report
        report_file = output_dir / "evolution_pattern_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("Method Evolution Pattern Analysis Report\n")
            f.write("=" * 80 + "\n\n")

            f.write("## Lifecycle Statistics\n")
            f.write(f"Total methods tracked: {lifecycle_stats['total_methods']}\n")
            f.write(
                f"Average lifespan: {lifecycle_stats['average_lifespan']:.2f} snapshots\n"
            )
            f.write(
                f"Short-lived methods (≤2 snapshots): {lifecycle_stats['short_lived']}\n"
            )
            f.write(
                f"Long-lived methods (≥10 snapshots): {lifecycle_stats['long_lived']}\n\n"
            )

            f.write("## Evolution Patterns\n")
            f.write(f"Renamed methods: {lifecycle_stats['renamed_methods']}\n")
            f.write(f"Moved methods: {lifecycle_stats['moved_methods']}\n")
            f.write(f"Refactored methods: {lifecycle_stats['refactored_methods']}\n\n")

            if stability_stats:
                f.write("## Stability Statistics\n")
                f.write(
                    f"Average stability: {stability_stats['average_stability']:.2%}\n"
                )
                f.write(
                    f"Highly stable methods (≥90%): {stability_stats['highly_stable']}\n"
                )
                f.write(f"Unstable methods (<50%): {stability_stats['unstable']}\n")

        self.logger.info(f"Report written to {report_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Analyze method evolution patterns from tracking data"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to method_tracking_details.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for analysis results",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="Log file path (optional)",
    )

    args = parser.parse_args()

    analyzer = EvolutionPatternAnalyzer(log_file=args.log)
    analyzer.load_tracking_details(args.input)
    analyzer.generate_report(args.output)


if __name__ == "__main__":
    main()
