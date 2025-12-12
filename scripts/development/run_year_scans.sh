#!/bin/bash
# Run overnight year-based scans for WPR.org bug detection
# Target years: 2019, 2020, 2021 (pre-migration era)

set -e

EXAMPLE_URL="https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail"
BASE_URL="https://www.wpr.org"
MAX_PAGES=10000

echo "Starting overnight year-based scans..."
echo "Target years: 2019, 2020, 2021"
echo "Max pages per scan: $MAX_PAGES"
echo "Start time: $(date)"

# Activate virtual environment
source .venv/bin/activate

# Scan 2019 content
echo ""
echo "=== Scanning 2019 content ==="
python -m src.analyzer.cli bug-finder scan \
  --example-url "$EXAMPLE_URL" \
  --site "$BASE_URL" \
  --max-pages $MAX_PAGES \
  --format all \
  --output bug_results_wpr_2019

# Scan 2020 content
echo ""
echo "=== Scanning 2020 content ==="
python -m src.analyzer.cli bug-finder scan \
  --example-url "$EXAMPLE_URL" \
  --site "$BASE_URL" \
  --max-pages $MAX_PAGES \
  --format all \
  --output bug_results_wpr_2020

# Scan 2021 content
echo ""
echo "=== Scanning 2021 content ==="
python -m src.analyzer.cli bug-finder scan \
  --example-url "$EXAMPLE_URL" \
  --site "$BASE_URL" \
  --max-pages $MAX_PAGES \
  --format all \
  --output bug_results_wpr_2021

echo ""
echo "All scans complete!"
echo "End time: $(date)"
echo ""
echo "Results saved to:"
echo "  - bug_results_wpr_2019.*"
echo "  - bug_results_wpr_2020.*"
echo "  - bug_results_wpr_2021.*"
