# Bug Finder Web Dashboard

A modern, responsive web-based dashboard for viewing and managing bug-finder scan results.

## Features

### Core Features
- **Project Overview**: View all projects with creation dates and last scan times
- **Scan History**: Browse all scans with status tracking (completed, running, error)
- **Interactive Results Viewer**:
  - Sortable and filterable bug lists
  - Paginated results
  - Real-time search across URLs
  - Expandable row details
- **Visual Analytics**:
  - Bug distribution charts (using Chart.js)
  - Statistics dashboard (total bugs, pages affected, averages)
  - Status breakdown visualizations
- **Pattern Management**:
  - Browse available patterns
  - Test patterns against content
  - View pattern details and severity levels
- **Export Functionality**:
  - JSON export for data integration
  - CSV export for spreadsheets
  - HTML export for sharing reports
  - Copy results to clipboard
- **Theme Support**: Light/dark mode toggle with system preference detection
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Installation

### Prerequisites
- Python 3.11+
- FastAPI
- Uvicorn

### Setup

```bash
# Install required packages
pip install fastapi uvicorn

# The dashboard is included with bug-finder CLI
```

## Usage

### Start the Dashboard

```bash
# Basic usage (starts on http://127.0.0.1:8000)
python -m src.analyzer.cli serve start

# Custom host and port
python -m src.analyzer.cli serve start --host 0.0.0.0 --port 3000

# Don't auto-open browser
python -m src.analyzer.cli serve start --no-browser

# Specify custom projects directory
python -m src.analyzer.cli serve start --base-dir /path/to/projects
```

### CLI Integration

The dashboard automatically:
- Reads scan results from the scan registry (`~/.bug-finder/scans.json`)
- Loads project metadata from `projects/` directory
- Updates in real-time as CLI scans complete

## Pages

### Home (`/`)
- **Project List**: All projects with creation dates and scan info
- **Recent Scans**: Latest scans with quick stats
- Quick navigation to individual projects

### Project Detail (`/project/<slug>`)
- Project metadata (URL, creation date, last crawl/scan)
- Scan history with status indicators
- Links to view full results

### Scan Results (`/scan/<scan_id>`)
- Detailed bug list with all matches
- Filtering by URL search term
- Sorting by match count or URL
- Pagination for large result sets
- Statistics and distribution charts
- Export options

### Patterns (`/patterns`)
- Browse all available patterns
- Pattern details (name, description, severity, tags)
- Test pattern against custom content
- Pattern management interface

### Settings (`/settings`)
- Display preferences (theme, items per page)
- Scan defaults (max pages, timeout)
- System information and diagnostics
- Keyboard shortcuts

## API Endpoints

The dashboard exposes REST APIs for integration:

```
GET  /api/health                      - Health check
GET  /api/projects                    - List projects
GET  /api/projects/<slug>             - Get project details
GET  /api/scans                       - List scans
GET  /api/scans/<id>                  - Get scan details
GET  /api/scans/<id>/results          - Get paginated results
GET  /api/scans/<id>/stats            - Get scan statistics
GET  /api/scans/<id>/export           - Export results
GET  /api/patterns                    - List patterns
GET  /api/patterns/<name>             - Get pattern details
```

### Query Parameters

**Scans Listing:**
- `limit` (int, default 50): Maximum scans to return
- `status` (str): Filter by status (completed, running, error, completed_clean)
- `project_slug` (str): Filter by project

**Results Pagination:**
- `page` (int, default 1): Page number
- `per_page` (int, default 20): Results per page
- `search` (str): Search term for URLs
- `sort_by` (str): Sort field (matches, url, status)
- `sort_order` (str): Sort order (asc, desc)

## Directory Structure

```
src/analyzer/web_ui/
├── __init__.py              # Module init
├── server.py                # FastAPI server and pages
├── api.py                   # API endpoints and data access
├── README.md                # This file
├── static/
│   ├── css/
│   │   └── style.css        # Main stylesheet
│   └── js/
│       ├── app.js           # Global app functionality
│       ├── home.js          # Home page script
│       ├── results.js       # Results page script
│       ├── patterns.js      # Patterns page script
│       └── settings.js      # Settings page script
└── templates/
    ├── index.html           # Home page
    ├── project.html         # Project detail
    ├── results.html         # Scan results
    ├── patterns.html        # Pattern management
    └── settings.html        # Settings page
```

## Styling

The dashboard uses a custom CSS framework with:
- **Variables**: Customizable colors and spacing
- **Dark Mode**: System preference detection with manual override
- **Responsive Grid**: Auto-adjusting layouts
- **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation

### Theme Colors
- Primary: #4CAF50 (Green)
- Secondary: #2196F3 (Blue)
- Danger: #f44336 (Red)
- Warning: #ff9800 (Orange)

## JavaScript Functionality

### Global (app.js)
- **ThemeManager**: Theme switching and persistence
- **API**: Centralized API communication
- **Utils**: Date formatting, notifications, utilities

### Home (home.js)
- Load and display scans
- Load and display projects
- Auto-refresh every 30 seconds

### Results (results.js)
- Render paginated results
- Handle filtering and sorting
- Generate charts
- Export functionality

### Patterns (patterns.js)
- Load pattern list
- Test pattern interface
- Pattern selection

### Settings (settings.js)
- Load/save preferences
- System information
- Keyboard shortcuts

## Features in Detail

### Filtering and Search

Results can be filtered by:
- **URL Search**: Substring matching on page URL
- **Match Count**: Sort by number of patterns found
- **Status**: Filter by match status

### Sorting

- **By Matches**: Most relevant results first
- **By URL**: Alphabetical ordering
- **Reverse Sorting**: All sort fields support ascending/descending

### Export Formats

1. **JSON**: Complete data structure for programmatic access
2. **CSV**: Spreadsheet-compatible format
3. **HTML**: Pretty-printed report for sharing
4. **Clipboard**: Copy table directly to clipboard
5. **Print**: Browser print functionality

### Charts and Statistics

The dashboard includes:
- **Distribution Chart**: Shows bug frequency across pages
- **Stat Cards**: Total bugs, pages affected, averages
- **Status Indicators**: Visual status badges with colors
- **Duration Tracking**: Shows scan completion time

## Performance

The dashboard is optimized for performance:
- Pagination limits default to 20-50 items per page
- CSS animations use GPU acceleration
- API responses are cached where appropriate
- Static files are minified

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Dashboard Won't Start
```bash
# Check if port is in use
lsof -i :8000

# Use different port
python -m src.analyzer.cli serve start --port 3000
```

### Missing Scan Data
```bash
# Verify scan registry exists
ls ~/.bug-finder/scans.json

# Check projects directory
ls projects/
```

### CSS/JS Not Loading
- Check static directory exists
- Verify web server is running properly
- Clear browser cache (Ctrl+Shift+Delete)

### Charts Not Rendering
- Ensure Chart.js is loading (check Network tab)
- Verify scan has results with proper data
- Check browser console for errors

## Development

### Running Locally

```bash
# Start server in development mode
python -m src.analyzer.cli serve start --no-browser

# Server runs on http://127.0.0.1:8000
```

### Adding New Pages

1. Create HTML in `templates/`
2. Create JavaScript in `static/js/`
3. Add route in `server.py`
4. Add API endpoint if needed

### Modifying Styles

Edit `static/css/style.css` and follow:
- Use CSS variables for colors
- Follow responsive grid patterns
- Include dark mode variants

## Security Considerations

- All user input is validated and escaped
- No sensitive credentials are stored in localStorage
- API endpoints don't expose sensitive system information
- CORS is not enabled (dashboard is same-origin only)

## Future Enhancements

- Real-time WebSocket updates
- Advanced analytics (trends, heatmaps)
- Scan scheduling UI
- Email notifications configuration
- Multi-user authentication
- Result comparison visualization
- Custom report generation

## License

Part of the Bug Finder project. See main LICENSE file.
