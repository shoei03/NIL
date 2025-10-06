# Analysis Directory

This directory contains Python scripts for analyzing CSV files in the results directory.

## Setup

The analysis environment runs in a separate Docker container with Python and data analysis libraries.

### Files

- `csv_line_count_analysis.py` - CSV line count analysis script
- `unique_clone_analyzer.py` - Code clone pair analysis script
- `test_analyzer.py` - Test script for the clone analyzer
- `run_analysis.sh` - Script to run CSV line count analysis
- `run_clone_analysis.sh` - Script to run clone analysis test
- `analyze_clones.sh` - Script to analyze any results CSV file
- `Dockerfile` - Docker configuration for Python environment
- `docker-compose.yml` - Docker Compose configuration
- `requirements.txt` - Python dependencies

## Usage

### 1. Run CSV Line Count Analysis

```bash
cd analysis
./run_analysis.sh
```

### 2. Run Code Clone Pair Analysis

#### Quick Test with Sample File

```bash
cd analysis
./run_clone_analysis.sh
```

#### Analyze Any Results File

```bash
cd analysis
./analyze_clones.sh /workspace/results/results_20120209_113131_71b65ab6.csv
```

#### Manual Analysis

```bash
cd analysis
docker compose up --build -d
docker compose exec analysis python unique_clone_analyzer.py /workspace/results/results_20120209_113131_71b65ab6.csv -o /app/output/output.csv -l /app/output/errors.log
docker compose down
```

### Command Line Options

- `input_csv` - Path to the input CSV file (required)
- `-o, --output` - Output CSV file path (optional, default: `<input>_with_ids.csv`)
- `-l, --log` - Log file path for error logging (optional, default: `clone_analyzer_errors_<timestamp>.log`)

### 3. Available Commands

List available result files:

```bash
cd analysis
docker compose exec analysis ls -la /workspace/results/
```

## Code Clone Analysis Features

The `unique_clone_analyzer.py` script:

- **Parses CSV files** containing code clone pairs in format: `file1,start1,end1,file2,start2,end2`
- **Assigns unique IDs** to each distinct clone pair
- **Detects duplicates** and reuses IDs for identical pairs
- **Normalizes pairs** by sorting to ensure consistent comparison
- **Generates detailed output** with pair IDs, occurrence flags, and hash values
- **Error logging** - All parsing and processing errors are logged to a file with timestamps

### Output Format

The analysis generates CSV files with these columns:

- `pair_id` - Unique identifier for each distinct clone pair
- `file1`, `start1`, `end1` - First code block location
- `file2`, `start2`, `end2` - Second code block location
- `is_first_occurrence` - True for first occurrence, False for duplicates
- `pair_hash` - MD5 hash for verification

## Output

Both analysis types generate files in the `output/` directory:

### CSV Line Count Analysis

1. **Console output** - Summary statistics
2. **output/csv_line_count_analysis.png** - Bar chart visualization
3. **output/line_count_summary.csv** - Detailed results in CSV format

### Code Clone Analysis

1. **Console output** - Analysis progress with tqdm progress bars
2. **output/\*\_with_ids.csv** - Processed data with unique IDs
3. **Log files** - Error logs with timestamps (if errors occur during processing)

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
