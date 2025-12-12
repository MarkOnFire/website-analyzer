# Bug Finder Web Dashboard - Complete Guide

## Overview

The Bug Finder Web Dashboard provides a modern, user-friendly interface for viewing and managing bug-finder scan results. It's a web-based alternative to the command-line interface, offering real-time visualization, filtering, sorting, and export capabilities.

## Quick Start

### Installation

The web dashboard is included with the bug-finder package. You only need to install the FastAPI dependencies:

```bash
pip install fastapi uvicorn
```

### Launch Dashboard

```bash
# Start on default port (8000)
python -m src.analyzer.cli serve start

# The browser will automatically open to http://127.0.0.1:8000
```

### Common Usage

```bash
# Use custom port
python -m src.analyzer.cli serve start --port 3000

# Allow external access
python -m src.analyzer.cli serve start --host 0.0.0.0 --port 8000

# Don't auto-open browser
python -m src.analyzer.cli serve start --no-browser
```

## Dashboard Pages

### 1. Home Page (/)

The landing page shows:
- **Recent Scans**: Latest 10 scans with status, bug count, and page count
- **Projects List**: All projects in your workspace with metadata

**Actions:**
- Click "View Results" on any scan card to see detailed results
- Click "View" on any project to see its scan history
- Search and filter through the project table

**Key Metrics:**
- Scan Status: completed, running, error, completed_clean
- Bug Count: total bugs found in scan
- Pages: number of pages scanned

### 2. Project Detail Page (/project/<slug>)

Shows information for a specific project:
- Project URL
- Creation date
- Last crawl timestamp
- Last scan timestamp
- Complete scan history table

**Features:**
- View scan history in a sortable table
- Click "View" to see detailed results for any scan
- Navigate back to home to see all projects

### 3. Scan Results Page (/scan/<scan_id>)

The main results page with detailed analysis:

**Controls:**
- **Search Box**: Filter results by URL (substring matching)
- **Sort Select**: Sort by matches (most/fewest) or URL (A-Z/Z-A)
- **Export Button**: Download results in multiple formats

**Statistics Section:**
- Total bugs found
- Pages affected
- Distribution chart (pie/doughnut chart)

**Results Table:**
- URL column: Clickable link to actual page
- Matches column: Number of matching patterns found
- Expandable rows: Click to see full URL and sample match

**Pagination:**
- Previous/Next buttons
- Current page indicator
- Auto-disabled buttons at boundaries

**Export Options:**
- JSON: Complete data structure for programmatic use
- CSV: Spreadsheet-compatible format
- HTML: Professional report for sharing
- Copy to Clipboard: Paste directly into documents
- Print: Browser print functionality

### 4. Patterns Page (/patterns)

Pattern management and testing interface:

**Pattern Browser:**
- Grid of all available patterns
- Pattern name, description, and severity level
- Tags and metadata display

**Test Interface:**
- Select pattern from dropdown
- Enter content to test against
- Execute test and view results
- Keyboard shortcut: Ctrl+Enter to test

**Pattern Details:**
- Name and description
- Severity level (low, medium, high, critical)
- Tags for categorization
- List of regex patterns included

### 5. Settings Page (/settings)

Configuration and preferences:

**Display Settings:**
- Theme: Light, Dark, or Auto (system default)
- Items per page: 5-100 (default 20)

**Scan Defaults:**
- Max pages: 10-10,000 (default 1000)
- Request timeout: 5-300 seconds (default 30)

**System Information:**
- Current status and API health
- Base directory path
- Browser information
- Local storage availability
- Keyboard shortcuts reference

**Storage:**
- All settings saved to browser local storage
- Persists across sessions
- Synced to browser preferences

## Data Visualization

### Charts

The dashboard includes interactive charts using Chart.js:

**Distribution Chart:**
- Shows bug frequency across pages
- Doughnut/pie chart format
- Color-coded slices
- Click legend to toggle data

### Statistics Cards

Real-time stats including:
- **Total Bugs**: Sum of all matches
- **Pages Affected**: Number of pages with bugs
- **Average Bugs/Page**: Total / pages
- **Match Distribution**: Frequency breakdown

## Search and Filter

### Quick Search

The search box on results page provides:
- Substring matching on URLs
- Case-insensitive search
- Real-time results update
- Search across all scanned pages

### Sorting Options

Results can be sorted by:
- **Most Matches**: Most relevant bugs first
- **Fewest Matches**: Less frequent bugs first
- **URL A-Z**: Alphabetical ascending
- **URL Z-A**: Alphabetical descending

### Pagination

- Default 20 results per page
- Customizable in settings (5-100)
- Previous/Next navigation
- Current page indicator
- Auto-disabled edge buttons

## Export Functionality

### JSON Export

```bash
# Downloaded as: scan_<id>_<date>.json
# Contains:
{
  "scan_id": "scan_001...",
  "exported_at": "2025-12-11T10:30:00",
  "results": [
    {
      "url": "https://example.com/page",
      "total_matches": 5,
      ...
    }
  ],
  "metadata": {...}
}
```

**Use Cases:**
- Data integration with other tools
- Programmatic analysis
- Version control (commit results)
- Automated reporting

### CSV Export

```bash
# Downloaded as: scan_<id>_<date>.csv
# Columns: url, total_matches, status, etc.
# Compatible with: Excel, Google Sheets, Numbers
```

**Use Cases:**
- Spreadsheet analysis
- Pivot tables
- Filtering and sorting in Excel
- Data visualization tools

### HTML Export

```bash
# Downloaded as: scan_<id>_<date>.html
# Standalone HTML file with:
# - Scan metadata
# - Professional styling
# - Complete results table
# - Print-friendly format
```

**Use Cases:**
- Email reports
- Share with stakeholders
- Archive for documentation
- Print to PDF

### Copy to Clipboard

- Click "Copy to Clipboard" in export menu
- Pastes formatted table directly
- Works with: Slack, email, documents, spreadsheets

### Print

- Standard browser print dialog
- Respects light/dark theme
- Page breaks for long tables
- Includes header and metadata

## Theme Support

### Light Mode
- Clean, professional appearance
- High contrast text
- Suitable for bright environments

### Dark Mode
- Easy on the eyes
- Reduced blue light
- Suitable for low-light environments

### Auto Mode (Default)
- Respects system preference
- iOS/macOS: Settings → Display & Brightness
- Windows 11: Settings → Personalization → Colors
- Linux: GNOME/KDE display settings

**Toggle:**
- Click moon/sun icon in header
- Saved to browser preferences
- Persists across sessions

## Keyboard Shortcuts

| Shortcut | Action | Page |
|----------|--------|------|
| Ctrl+E | Open export menu | Results |
| Ctrl+P | Print results | Results |
| Ctrl+Enter | Test pattern | Patterns |
| Ctrl+K | Focus search (future) | All |
| Tab | Navigate form fields | Settings |
| Enter | Save settings | Settings |

## Real-Time Updates

The dashboard automatically:
- Updates every 30 seconds on home page
- Refreshes project scan history
- Reflects new scans from CLI
- Shows latest statistics

**Note:** Refresh browser manually if updates don't appear.

## API Integration

Developers can access the dashboard APIs directly:

```bash
# List all scans
curl http://127.0.0.1:8000/api/scans

# Get specific scan
curl http://127.0.0.1:8000/api/scans/scan_001

# Get paginated results
curl "http://127.0.0.1:8000/api/scans/scan_001/results?page=1&per_page=50"

# Search results
curl "http://127.0.0.1:8000/api/scans/scan_001/results?search=example.com"

# Get statistics
curl http://127.0.0.1:8000/api/scans/scan_001/stats

# Export as JSON
curl http://127.0.0.1:8000/api/scans/scan_001/export?format=json
```

## Workflow Examples

### Scenario 1: Monitoring a Website

```bash
# 1. Run bug-finder scan from CLI
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/web/.../buggy-page" \
  --site "https://mysite.com" \
  --max-pages 500

# 2. Open dashboard
python -m src.analyzer.cli serve start

# 3. View latest scan on home page
# 4. Click "View Results" to see affected pages
# 5. Export as HTML to share with team
# 6. Create follow-up scan after fixes to compare
```

### Scenario 2: Tracking Bug Fixes

```bash
# 1. Load dashboard
python -m src.analyzer.cli serve start

# 2. Click on a project to see scan history
# 3. Note bug count in previous scans
# 4. After making fixes, run new scan
# 5. Compare new results with previous scan
# 6. Use bug-finder compare command to see improvements
```

### Scenario 3: Investigating a Specific Bug

```bash
# 1. Open dashboard and view scan results
# 2. Click on affected page URL to visit it
# 3. Inspect HTML to understand the bug
# 4. Use Patterns page to test fix patterns
# 5. Export results for documentation
# 6. Create pattern for this bug type
```

### Scenario 4: Team Collaboration

```bash
# 1. Run scan and let it complete
# 2. Open dashboard
# 3. Export results as HTML
# 4. Share HTML file via email or Slack
# 5. Team members open in browser
# 6. Discuss affected pages and next steps
```

## Performance Tips

### For Large Scans (1000+ pages)

1. **Use Pagination**
   - Default 20 per page is efficient
   - Don't increase to 100+ for large result sets

2. **Filter First**
   - Search for specific domain to reduce results
   - Export only relevant results

3. **Browser Optimization**
   - Use modern browser (Chrome/Firefox)
   - Close other tabs to free memory
   - Enable browser caching

4. **Server Configuration**
   - Run on local machine for best performance
   - Use `--host 127.0.0.1` (default)
   - Avoid network latency

### For Remote Access

```bash
# If running on server and accessing remotely:
python -m src.analyzer.cli serve start --host 0.0.0.0 --port 8000

# Access from other machine:
# http://<server-ip>:8000
```

## Troubleshooting

### Dashboard Won't Start

**Error: "Port 8000 already in use"**
```bash
# Check what's using the port
lsof -i :8000

# Use different port
python -m src.analyzer.cli serve start --port 3000
```

**Error: "FastAPI not installed"**
```bash
# Install required dependencies
pip install fastapi uvicorn
```

### Data Not Showing

**No scans visible:**
```bash
# Verify scan registry exists
ls ~/.bug-finder/scans.json

# Verify projects directory
ls projects/
```

**Partial data:**
- Refresh browser (Ctrl+R)
- Wait 30 seconds for auto-refresh
- Check if scan completed successfully

### UI Issues

**CSS not loading (styling broken):**
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh (Ctrl+Shift+R)
- Check static directory exists
- Restart server

**Charts not showing:**
- Verify scan has results
- Check browser console (F12)
- Ensure JavaScript is enabled

**Slow performance:**
- Check internet connection
- Reduce items per page in settings
- Close browser tabs
- Restart browser

## Security & Privacy

### Data Handling

- All data is read-only through the dashboard
- No scan modifications through web UI
- Results are local (not sent anywhere)
- Theme preferences stored in browser only

### Access Control

- Dashboard is local-only by default (127.0.0.1)
- For remote access, set `--host 0.0.0.0`
- Consider using VPN or SSH tunnel for remote access
- No authentication mechanism (add reverse proxy if needed)

### Data Storage

- Results read from disk
- No sensitive info stored in browser
- Scan registry is readable but not modified
- Local storage only for preferences

## Advanced Features

### Pattern Testing

```
1. Go to /patterns page
2. Select a pattern from dropdown
3. Paste or enter content to test
4. Click "Test Pattern"
5. View matches and statistics
```

### Custom Export

Use API directly for custom exports:

```bash
# Export with filters
curl "http://127.0.0.1:8000/api/scans/scan_001/results?search=domain.com&sort_by=matches&sort_order=desc" > results.json

# Programmatic integration
import requests
results = requests.get('http://127.0.0.1:8000/api/scans/scan_001/results').json()
```

### Extend the Dashboard

The codebase is designed for extension:
- Add new pages by editing `server.py`
- Implement new API endpoints in `api.py`
- Modify styling in `style.css`
- Add functionality in JavaScript files

## Performance Specifications

- **Typical Load Time**: < 1 second
- **Search Response**: < 100ms
- **Chart Rendering**: < 500ms
- **Pagination**: < 50ms
- **Export Generation**: < 1 second (small), < 10 seconds (large)

## Browser Requirements

- **Minimum**: ES6 JavaScript support
- **Recommended**: Modern browser (released in last 2 years)
- **Tested**: Chrome 120+, Firefox 121+, Safari 17+, Edge 121+

## Support & Feedback

For issues or feature requests:
1. Check troubleshooting section above
2. Review dashboard logs
3. Check browser console (F12)
4. Create issue with example scan data

## Related Documentation

- See `src/analyzer/web_ui/README.md` for technical documentation
- See CLI documentation for scan commands
- See API documentation for programmatic access

---

**Last Updated:** December 2025
**Version:** 1.0.0
