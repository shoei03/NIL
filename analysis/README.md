# Analysis Directory

This directory contains Python scripts for analyzing CSV files in the results directory.

## Setup

The analysis environment runs in a separate Docker container with Python and data analysis libraries.

### Files

- `csv_line_count_analysis.py` - Main analysis script
- `Dockerfile` - Docker configuration for Python environment
- `docker-compose.yml` - Docker Compose configuration
- `requirements.txt` - Python dependencies
- `run_analysis.sh` - Convenience script to run the analysis

## Usage

### Run CSV Line Count Analysis

```bash
cd analysis
./run_analysis.sh
```

Or manually:

```bash
cd analysis
docker compose build
docker compose run --rm analysis python csv_line_count_analysis.py
```

### Output

The analysis generates files in the `output/` directory:

1. **Console output** - Summary statistics
2. **output/csv_line_count_analysis.png** - Bar chart visualization
3. **output/line_count_summary.csv** - Detailed results in CSV format

### Features

- Counts lines in all CSV files in the results directory
- Creates bar chart showing line count per file
- Shows time series analysis if dates can be extracted from filenames
- Provides summary statistics (total, average, min, max lines)
- Saves results for further analysis

## Requirements

- Docker and Docker Compose
- CSV files in the `../results` directory

## Docker Environment

The analysis runs in an isolated Python environment with:

- Python 3.11
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- numpy >= 1.24.0

The results directory is mounted as a volume, so the analysis can access CSV files without copying them into the container.
