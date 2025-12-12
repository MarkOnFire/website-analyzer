# Bug Finder Web Dashboard - Quick Start

## In 5 Minutes

### 1. Install Dependencies
```bash
pip install fastapi uvicorn
```

### 2. Start Dashboard
```bash
python -m src.analyzer.cli serve start
```

Your browser will automatically open to `http://127.0.0.1:8000`

### 3. View Your First Scan
- Dashboard opens on Home page
- You'll see projects and recent scans (if any exist)
- Click "View Results" to see scan details

### 4. Run a Scan (CLI)
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/web/.../page-with-bug" \
  --site "https://mysite.com" \
  --max-pages 100
```

### 5. Refresh Dashboard
- The dashboard auto-updates every 30 seconds
- Or refresh browser (Ctrl+R) to see latest scan immediately

## Pages Overview

### Home (/)
Shows all projects and recent scans at a glance.

### Project Detail (/project/<slug>)
Shows scan history for a specific project.

### Scan Results (/scan/<scan_id>)
Interactive results with:
- Search by URL
- Sort by matches or URL
- Pagination (20 per page)
- Charts and statistics
- Export options

### Patterns (/patterns)
Browse and test bug patterns.

### Settings (/settings)
Configure theme, display, and scan defaults.

## Common Tasks

### Search Results
1. Go to scan results page
2. Type in "Search URLs..." box
3. Results filter in real-time

### Sort Results
1. Click "Sort Select" dropdown
2. Choose: Most Matches, Fewest Matches, URL A-Z, URL Z-A

### Export Results
1. Click "Export" button
2. Choose format: JSON, CSV, HTML, Clipboard, Print
3. File downloads or opens in new window

### Toggle Dark Mode
1. Click moon/sun icon in header
2. Theme applies immediately
3. Preference saved for next visit

### Change Display Settings
1. Go to Settings page
2. Adjust theme, items per page, scan defaults
3. Click "Save Settings"

## Command Options

### Start on Custom Port
```bash
python -m src.analyzer.cli serve start --port 3000
```

### Allow Remote Access
```bash
python -m src.analyzer.cli serve start --host 0.0.0.0 --port 8000
```

### Don't Auto-Open Browser
```bash
python -m src.analyzer.cli serve start --no-browser
```

### Use Different Projects Directory
```bash
python -m src.analyzer.cli serve start --base-dir /path/to/projects
```

## Troubleshooting

### Port Already In Use
```bash
# Use different port
python -m src.analyzer.cli serve start --port 3000
```

### CSS/JS Not Loading
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+R)
3. Restart server

### No Data Showing
1. Run a scan first: `bug-finder scan ...`
2. Wait for scan to complete
3. Refresh dashboard page

### Slow Performance
1. Reduce items per page in settings
2. Search to filter results
3. Close other browser tabs

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+E | Export menu (results page) |
| Ctrl+P | Print results |
| Ctrl+Enter | Test pattern (patterns page) |

## API Usage

Quick API queries:

```bash
# List projects
curl http://127.0.0.1:8000/api/projects

# List scans
curl http://127.0.0.1:8000/api/scans

# Get scan results
curl "http://127.0.0.1:8000/api/scans/scan_001/results"

# Export as JSON
curl http://127.0.0.1:8000/api/scans/scan_001/export?format=json > results.json
```

## Features At A Glance

✓ Home page with projects and scans
✓ Interactive results viewer
✓ Real-time search and filter
✓ Sortable results
✓ Paginated browsing
✓ Distribution charts
✓ Statistics dashboard
✓ Export (JSON, CSV, HTML, clipboard, print)
✓ Dark/light theme
✓ Mobile responsive
✓ Pattern management
✓ Settings/preferences

## File Locations

**Configuration**: No setup needed! Just install and run.

**Data Read From**:
- Scan registry: `~/.bug-finder/scans.json`
- Projects: `./projects/` directory

**Static Files**: Served from `src/analyzer/web_ui/static/`

## Browser Support

Works on:
- Chrome 120+
- Firefox 121+
- Safari 17+
- Edge 121+
- Mobile browsers

## Next Steps

1. Try filtering and sorting results
2. Export in different formats
3. Test the patterns page
4. Toggle dark mode
5. Customize settings
6. Share results with team (export HTML)

## Need Help?

- Check `/src/analyzer/web_ui/README.md` for technical details
- See `WEB_DASHBOARD_GUIDE.md` for detailed user guide
- Review `WEB_DASHBOARD_SUMMARY.md` for full documentation

## Performance Tips

- Dashboard loads in < 1 second
- Search filters in < 100ms
- Charts render in < 500ms
- Default page size (20 items) is efficient
- Pagination avoids loading all results at once

## Security Notes

- Local access only by default
- No authentication mechanism
- Use `--host 0.0.0.0` for network access
- Consider VPN or reverse proxy for remote access
- All data stays on local machine

## What You Can Do

With the dashboard, you can:
- View all scan results visually
- Search for specific pages
- Sort by relevance or URL
- See statistics and charts
- Export for reports
- Test patterns
- Configure preferences
- Share results with team
- Integrate via API

## Limitations

- No real-time WebSocket updates (page auto-refresh)
- No scan scheduling from UI (use CLI)
- No result modification (read-only)
- Single user (add auth if needed)

## Customization

Easy to modify:
- **Colors**: Edit `static/css/style.css`
- **Layout**: Modify CSS Grid
- **Pages**: Extend `server.py`
- **API**: Add endpoints in `api.py`
- **Scripts**: Update JavaScript files

---

**Ready?** Start with: `python -m src.analyzer.cli serve start`

Then visit: `http://127.0.0.1:8000`
