#!/usr/bin/env python3
"""
CSV Line Count Analysis

This script analyzes CSV files in the results directory and creates a bar chart
showing the number of lines in each file.
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def get_csv_files(input_dir):
    """Get all CSV files from the results directory."""
    results_path = Path(input_dir)
    return list(results_path.glob("*.csv"))


def count_lines_in_csv(file_path):
    """Count the number of lines in a CSV file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return sum(1 for line in f)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return 0


def extract_date_from_filename(filename):
    """Extract date from filename format: results_YYYYMMDD_HHMMSS_hash.csv"""
    basename = Path(filename).name
    if basename.startswith("results_") and basename.endswith(".csv"):
        try:
            # Extract date part: YYYYMMDD
            date_part = basename.split("_")[1]
            return datetime.strptime(date_part, "%Y%m%d")
        except (IndexError, ValueError):
            return None
    return None


def analyze_csv_files(input_dir, output_dir):
    """Main analysis function."""
    # Get all CSV files
    csv_files = get_csv_files(input_dir)

    if not csv_files:
        logging.warning("No CSV files found in the results directory.")
        return

    logging.info(f"Found {len(csv_files)} CSV files")

    # Count lines in each file
    file_data = []
    for file_path in csv_files:
        line_count = count_lines_in_csv(file_path)
        date = extract_date_from_filename(file_path)
        file_data.append(
            {
                "filename": Path(file_path).name,
                "line_count": line_count,
                "date": date,
                "file_path": file_path,
            }
        )

    # Create DataFrame
    df = pd.DataFrame(file_data)
    df = df.sort_values("date") if "date" in df.columns else df.sort_values("filename")

    # Print summary
    logging.info("\nSummary:")
    logging.info(f"Total files: {len(df)}")
    logging.info(f"Total lines: {df['line_count'].sum():,}")
    logging.info(f"Average lines per file: {df['line_count'].mean():.1f}")
    logging.info(f"Min lines: {df['line_count'].min()}")
    logging.info(f"Max lines: {df['line_count'].max()}")

    # Create visualization
    plt.style.use("seaborn-v0_8")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

    # Bar chart by filename
    ax1.bar(range(len(df)), df["line_count"], alpha=0.7, color="steelblue")
    ax1.set_xlabel("CSV Files (chronological order)")
    ax1.set_ylabel("Number of Lines")
    ax1.set_title("Line Count per CSV File in Results Directory")
    ax1.grid(True, alpha=0.3)

    # Set x-axis labels (show every nth label to avoid overcrowding)
    step = max(1, len(df) // 20)  # Show at most 20 labels
    indices = range(0, len(df), step)
    ax1.set_xticks(indices)
    ax1.set_xticklabels(
        [
            df.iloc[i]["filename"][:15] + "..."
            if len(df.iloc[i]["filename"]) > 15
            else df.iloc[i]["filename"]
            for i in indices
        ],
        rotation=45,
        ha="right",
    )

    # Time series chart (if dates are available)
    if df["date"].notna().any():
        valid_dates = df[df["date"].notna()]
        ax2.plot(
            valid_dates["date"],
            valid_dates["line_count"],
            marker="o",
            linestyle="-",
            alpha=0.7,
            color="darkgreen",
        )
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Number of Lines")
        ax2.set_title("Line Count Over Time")
        ax2.grid(True, alpha=0.3)

        # Format x-axis dates
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")
    else:
        ax2.text(
            0.5,
            0.5,
            "Date information not available",
            ha="center",
            va="center",
            transform=ax2.transAxes,
        )
        ax2.set_title("Time Series Analysis (No Date Info)")

    plt.tight_layout()

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save the plot
    output_file = output_path / "csv_line_count_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logging.info(f"Visualization saved as: {output_file}")

    # Show the plot
    plt.show()

    # Save detailed results to CSV
    output_csv = output_path / "line_count_summary.csv"
    df.to_csv(output_csv, index=False)
    logging.info(f"Detailed results saved as: {output_csv}")

    return df


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze CSV files and create visualizations of line counts."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="/workspace/results",
        help="Input directory containing CSV files (default: /workspace/results)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        help="Output directory for results and visualizations (default: output)",
    )
    parser.add_argument(
        "--log",
        "-l",
        type=str,
        default="logs/csv_line_count_analysis.log",
        help="Log file path (default: logs/csv_line_count_analysis.log)",
    )
    return parser.parse_args()


def setup_logging(log_file):
    """Setup logging configuration."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()

    # Setup logging
    setup_logging(args.log)

    logging.info("CSV Line Count Analysis")
    logging.info("=" * 50)

    # Check if results directory exists
    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"Error: '{args.input}' directory not found.")
        logging.error("Make sure the directory exists and the path is correct.")
        exit(1)

    logging.info(f"Input directory: {args.input}")
    logging.info(f"Output directory: {args.output}")
    logging.info(f"Log file: {args.log}")
    logging.info("")

    # Run analysis
    df = analyze_csv_files(args.input, args.output)
