#!/bin/bash

# CSV Line Count Analysis Runner
# This script builds and runs the analysis in Docker

echo "Building analysis Docker environment..."
docker compose build

echo "Running CSV line count analysis..."
docker compose run --rm analysis python csv_line_count_analysis.py

echo "Analysis complete!"
echo "Check the generated files in the output/ directory:"
echo "  - output/csv_line_count_analysis.png (visualization)"
echo "  - output/line_count_summary.csv (detailed results)"