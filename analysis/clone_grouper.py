#!/usr/bin/env python3
"""
Clone pairs をグループ化し、各 run ディレクトリに clone_groups.csv を生成するスクリプト。

Requirements:
    - Python 3.14+
    - pandas, pathlib, logging, tqdm
    
Input:
    - analysis/output/results_index.json (run情報)
    - results/{run_id}/clone_pairs.csv (各runのクローンペア)
    
Output:
    - results/{run_id}/clone_groups.csv (同じディレクトリ内)
"""

import json
import logging
import sys
from pathlib import Path
from typing import TypedDict

import networkx as nx
import pandas as pd
from tqdm import tqdm
from utils.logging_utils import setup_logging


# Type Definitions
class RunInfo(TypedDict):
    """Run directory metadata."""
    run_id: str
    datetime: str
    hash: str
    dir: str
    files: dict[str, dict[str, str | int]]


class ProcessResult(TypedDict):
    """Processing result for a single run."""
    run_id: str
    success: bool
    input_rows: int
    output_rows: int
    error: str | None


# Constants
INDEX_PATH: Path = Path(__file__).parent / "output" / "results_index.json"
RESULTS_ROOT: Path = Path(__file__).parents[1] / "results"
LOG_PATH: Path = Path(__file__).parent / "logs" / "group_clone_pairs.log"

INPUT_FILENAME = "clone_pairs.csv"
OUTPUT_FILENAME = "clone_groups.csv"


def load_index() -> list[RunInfo]:
    """
    Load run information from results_index.json.
    
    Returns:
        List of RunInfo dictionaries.
        
    Raises:
        FileNotFoundError: If index file does not exist.
        json.JSONDecodeError: If index file is malformed.
    """
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Index file not found: {INDEX_PATH}")
    
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    runs = data.get("runs", [])
    logging.info("Loaded %d runs from index", len(runs))
    return runs


def group_clone_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group clone pairs into connected components using NetworkX.
    
    Algorithm:
        1. Build undirected graph from method pairs
        2. Find connected components
        3. Assign group IDs to each component
    
    Args:
        df: DataFrame with columns [method_id_1, method_id_2, ngram_similarity, lcs_similarity]
        
    Returns:
        DataFrame with columns [group_id, method_id, group_size]
    """
    if df.empty:
        logging.warning("Empty input DataFrame, returning empty result")
        return pd.DataFrame(columns=["group_id", "method_id", "group_size"])
    
    # Assume first two columns are method IDs
    col_method1 = df.columns[0]
    col_method2 = df.columns[1]
    
    logging.debug("Building graph from %d pairs", len(df))
    
    # Build undirected graph
    G = nx.Graph()
    for _, row in df.iterrows():
        method1 = row[col_method1]
        method2 = row[col_method2]
        G.add_edge(method1, method2)
    
    logging.debug("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    
    # Find connected components
    components = list(nx.connected_components(G))
    logging.info("Found %d clone groups", len(components))
    
    # Build output DataFrame
    rows = []
    for group_id, component in enumerate(components, start=1):
        group_size = len(component)
        for method_id in sorted(component):  # Sort for deterministic output
            rows.append({
                "group_id": group_id,
                "method_id": method_id,
                "group_size": group_size,
            })
    
    result_df = pd.DataFrame(rows)
    
    # Log group size distribution
    if not result_df.empty:
        size_dist = result_df.groupby("group_id")["group_size"].first().value_counts().sort_index()
        logging.debug("Group size distribution:")
        for size, count in size_dist.items():
            logging.debug("  Size %d: %d groups", size, count)
    
    return result_df


def validate_input(df: pd.DataFrame) -> bool:
    """
    Validate input DataFrame structure.
    
    Args:
        df: Input DataFrame to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if df.empty:
        logging.warning("Input DataFrame is empty")
        return False
    
    # Check minimum columns (at least 2 for method IDs)
    if len(df.columns) < 2:
        logging.error("Input must have at least 2 columns (method_id_1, method_id_2)")
        return False
    
    # Check for null values in method ID columns
    if df.iloc[:, :2].isnull().any().any():
        logging.warning("Found null values in method ID columns")
        return False
    
    logging.debug("Input validation passed: %d rows, %d columns", len(df), len(df.columns))
    return True


def process_run(run_info: RunInfo) -> ProcessResult:
    """
    Process a single run: read clone_pairs.csv, group, and write clone_groups.csv.
    
    Args:
        run_info: Run metadata from index.
        
    Returns:
        ProcessResult containing success status and metrics.
    """
    run_id = run_info["run_id"]
    run_dir = RESULTS_ROOT / run_id
    input_path = run_dir / INPUT_FILENAME
    output_path = run_dir / OUTPUT_FILENAME
    
    result: ProcessResult = {
        "run_id": run_id,
        "success": False,
        "input_rows": 0,
        "output_rows": 0,
        "error": None,
    }
    
    # Check input file existence
    if not input_path.exists():
        result["error"] = f"Input file not found: {input_path}"
        logging.warning("Skipping %s: %s", run_id, result["error"])
        return result
    
    try:
        # Read input
        df_input = pd.read_csv(input_path)
        result["input_rows"] = len(df_input)
        
        # Validate
        if not validate_input(df_input):
            result["error"] = "Input validation failed"
            logging.warning("Validation failed for %s", run_id)
            return result
        
        # Process
        df_output = group_clone_pairs(df_input)
        result["output_rows"] = len(df_output)
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_output.to_csv(output_path, index=False)
        
        result["success"] = True
        logging.info(
            "Processed %s: %d -> %d rows",
            run_id,
            result["input_rows"],
            result["output_rows"],
        )
        
    except pd.errors.EmptyDataError as e:
        result["error"] = f"Empty or malformed CSV: {e}"
        logging.error("Failed to read %s: %s", input_path, e)
    except Exception as e:  # pylint: disable=broad-except
        result["error"] = str(e)
        logging.error(
            "Error processing %s: %s",
            run_id,
            e,
            exc_info=True,
        )
    
    return result


def generate_summary(results: list[ProcessResult]) -> dict[str, int]:
    """
    Generate processing summary statistics.
    
    Args:
        results: List of processing results.
        
    Returns:
        Dictionary containing summary metrics.
    """
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    total_input_rows = sum(r["input_rows"] for r in results if r["success"])
    total_output_rows = sum(r["output_rows"] for r in results if r["success"])
    
    return {
        "total_runs": total,
        "successful": successful,
        "failed": failed,
        "total_input_rows": total_input_rows,
        "total_output_rows": total_output_rows,
    }


def main() -> int:
    """
    Main execution flow.
    
    Returns:
        Exit code (0: success, 1: failure).
    """
    try:
        setup_logging(LOG_PATH)
        logging.info("=" * 60)
        logging.info("Starting clone pairs grouping")
        
        # Load index
        runs = load_index()
        
        if not runs:
            logging.warning("No runs found in index")
            return 0
        
        # Process all runs
        results: list[ProcessResult] = []
        for run_info in tqdm(runs, desc="Processing runs", unit="run"):
            result = process_run(run_info)
            results.append(result)
        
        # Generate summary
        summary = generate_summary(results)
        
        # Log summary
        logging.info("=" * 60)
        logging.info("Processing completed")
        logging.info("  Total runs: %d", summary["total_runs"])
        logging.info("  Successful: %d", summary["successful"])
        logging.info("  Failed: %d", summary["failed"])
        logging.info("  Total input rows: %d", summary["total_input_rows"])
        logging.info("  Total output rows: %d", summary["total_output_rows"])
        logging.info("=" * 60)
        
        # Log failures
        if summary["failed"] > 0:
            logging.warning("Failed runs:")
            for result in results:
                if not result["success"]:
                    logging.warning("  %s: %s", result["run_id"], result["error"])
        
        return 0 if summary["failed"] == 0 else 1
        
    except FileNotFoundError as e:
        logging.error("File not found: %s", e)
        return 1
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Unexpected error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())