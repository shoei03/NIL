# Analysis Directory

This directory contains Python scripts for analyzing CSV files in the results directory.

## Setup

The analysis environment runs in a separate Docker container with Python and data analysis libraries.

### Files

- `csv_line_count_analysis.py` - CSV line count analysis script with logging
- `unique_clone_analyzer.py` - Code clone pair analysis script with batch processing
- `pair_diff.py` - Analyze differences in method pairs between snapshots
- `method_tracker.py` - Track methods across snapshots (exact matching)
- `test_analyzer.py` - Test script for the clone analyzer
- `run_analysis.sh` - Legacy script to run CSV line count analysis
- `run_clone_analysis.sh` - Legacy script to run clone analysis test
- `analyze_clones.sh` - Legacy script to analyze any results CSV file
- `Dockerfile` - Docker configuration for Python environment
- `docker-compose.yml` - Docker Compose configuration
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Usage

### 1. Method Evolution Tracking (NEW)

Track methods across snapshots using exact matching (file path, method name, signature).

#### Requirements

- NIL must be run with `--commit-hash` option to generate `code_blocks_<hash>` files in `code_blocks/` directory
- Multiple `code_blocks_*` files in the `code_blocks/` subdirectory of the input directory

#### Basic Usage

```bash
cd analysis
docker compose run --rm analysis python method_tracker.py \
  -i /workspace \
  -o /app/output/method_tracking
```

#### Command Line Options

- `-i, --input` - Directory containing code*blocks*\* files (required)
- `-o, --output` - Output directory for tracking results (required)
- `--log` - Log file path (optional)

#### Output Files

- `method_tracking_summary.csv` - Summary statistics per snapshot pair
  - Columns: snapshot_t, snapshot_t1, exact_matches, added_methods, deleted_methods, total_t, total_t1
- `method_tracking_details.csv` - Detailed change information
  - Columns: snapshot_t, snapshot_t1, change_type, file_path, method_name, signature, line_range_t, line_range_t1, commit_t, commit_t1

#### Example

```bash
# Run NIL with batch mode to generate code_blocks files
cd /path/to/NIL
./scripts/nil.sh /app/Repos/pandas --batch --skip 1000

# Track methods across snapshots
cd analysis
docker compose run --rm analysis python method_tracker.py \
  -i /workspace \
  -o /app/output/method_tracking \
  --log /app/logs/method_tracker.log
```

### 2. Run CSV Line Count Analysis

The CSV line count analysis script supports command-line arguments for flexible usage.

#### Basic Usage

```bash
cd analysis
docker compose run --rm analysis python csv_line_count_analysis.py
```

#### With Custom Paths

```bash
cd analysis
docker compose run --rm analysis python csv_line_count_analysis.py \
  --input /workspace/results \
  --output /app/output \
  --log /app/logs/analysis.log
```

#### Command Line Options for CSV Line Count Analysis

- `-i, --input` - Input directory containing CSV files (default: `/workspace/results`)
- `-o, --output` - Output directory for results and visualizations (default: `output`)
- `-l, --log` - Log file path (default: `logs/csv_line_count_analysis.log`)

#### Legacy Script

```bash
cd analysis
./run_analysis.sh
```

### 2. Run Code Clone Pair Analysis

The clone analyzer processes all CSV files in a directory and assigns unique IDs to code clone pairs.

#### Process All Files in a Directory

```bash
cd analysis
docker compose run --rm analysis python unique_clone_analyzer.py
```

This will:

- Process all CSV files in `/workspace/results` (default)
- Overwrite the original files with analyzed data
- Log to `logs/clone_analyzer.log`

#### With Custom Paths

```bash
cd analysis
docker compose run --rm analysis python unique_clone_analyzer.py \
  --input-dir /workspace/results \
  --output-dir /app/output \
  --log /app/logs/clone_analysis.log
```

#### Command Line Options for Clone Analysis

- `-i, --input-dir` - Input directory containing CSV files (default: `../results`)
- `-o, --output-dir` - Output directory for processed CSV files (default: same as input_dir, overwrites originals)
- `-l, --log` - Log file path (default: `logs/clone_analyzer.log`)

#### Legacy Scripts

Quick Test with Sample File:

```bash
cd analysis
./run_clone_analysis.sh
```

Analyze Any Results File:

```bash
cd analysis
./analyze_clones.sh /workspace/results/results_20120209_113131_71b65ab6.csv
```

### 3. Available Commands

List available result files:

```bash
cd analysis
docker compose exec analysis ls -la /workspace/results/
```

## Code Clone Analysis Features

The `unique_clone_analyzer.py` script:

- **Processes multiple files** - Analyzes all CSV files in a directory
- **Parses CSV files** containing code clone pairs in format: `file1,start1,end1,file2,start2,end2`
- **Assigns unique IDs** to each distinct clone pair within each file
- **Detects duplicates** and reuses IDs for identical pairs
- **Normalizes pairs** by sorting to ensure consistent comparison
- **Generates detailed output** with pair IDs, occurrence flags, and hash values
- **Comprehensive logging** - All operations, progress, and errors are logged to file and console with timestamps
- **Progress tracking** - Uses tqdm for visual progress bars during processing

### Output Format

The analysis generates CSV files with these columns:

- `pair_id` - Unique identifier for each distinct clone pair
- `file1`, `start1`, `end1` - First code block location
- `file2`, `start2`, `end2` - Second code block location
- `is_first_occurrence` - True for first occurrence, False for duplicates
- `pair_hash` - MD5 hash for verification

### Logging

Both scripts use Python's `logging` module with the following features:

- **Dual output** - Logs are written to both file and console
- **Timestamped entries** - Format: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`
- **Multiple log levels** - INFO for general progress, WARNING for issues, ERROR for failures
- **Automatic directory creation** - Log directories are created if they don't exist
- **UTF-8 encoding** - Ensures proper handling of all characters

## Output

Both analysis types generate files in the `output/` and `logs/` directories:

### CSV Line Count Analysis Output

1. **Console and log output** - Real-time progress and summary statistics
2. **output/csv_line_count_analysis.png** - Bar chart and time series visualization
3. **output/line_count_summary.csv** - Detailed results in CSV format with all file statistics
4. **logs/csv_line_count_analysis.log** - Complete execution log with timestamps

Example log output:

```
2025-10-06 05:16:29,227 - INFO - CSV Line Count Analysis
2025-10-06 05:16:29,227 - INFO - ==================================================
2025-10-06 05:16:29,228 - INFO - Found 36 CSV files
2025-10-06 05:16:29,294 - INFO - Total files: 36
2025-10-06 05:16:29,294 - INFO - Total lines: 238,537
```

### Code Clone Analysis Output

1. **Console and log output** - Analysis progress with tqdm progress bars and status messages
2. **Processed CSV files** - Original files overwritten (or new files if output directory specified) with unique IDs added
3. **logs/clone_analyzer.log** - Complete execution log including all operations, warnings, and errors

Example log output:

```
2025-10-06 14:30:15,123 - INFO - Found 36 CSV files to process in /workspace/results
2025-10-06 14:30:15,124 - INFO - Output directory: /workspace/results
2025-10-06 14:30:45,678 - INFO - All files processed successfully!
```

## Requirements

- Docker and Docker Compose
- CSV files in the `../results` directory

## Key Improvements

Both analysis scripts now feature:

- **pathlib usage** - Modern Python path handling with `Path` objects instead of `os.path`
- **Comprehensive logging** - All output goes to both console and log files
- **Flexible configuration** - Command-line arguments for all input/output paths
- **Automatic directory creation** - Output and log directories created as needed
- **UTF-8 encoding** - Proper handling of international characters
- **Error handling** - Graceful error recovery with detailed logging

## Docker Environment

The analysis runs in an isolated Python environment with:

- Python 3.11
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- numpy >= 1.24.0

The results directory is mounted as a volume, so the analysis can access CSV files without copying them into the container.
