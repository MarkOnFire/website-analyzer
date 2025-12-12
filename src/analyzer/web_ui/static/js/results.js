/**
 * Results Page Script
 *
 * Handles:
 * - Loading and displaying scan results
 * - Filtering and sorting
 * - Statistics and charts
 * - Export functionality
 */

// This script works with inline JavaScript defined in server.py
// Additional functionality can be added here as needed

/**
 * Common export handler
 */
async function handleExport(format) {
    if (typeof scanId === 'undefined') return;

    try {
        Utils.notify('Preparing export...', 'info');
        const link = document.createElement('a');
        link.href = `/api/scans/${scanId}/export?format=${format}`;
        link.download = `scan_${scanId}_${new Date().toISOString().slice(0, 10)}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        Utils.notify('Export downloaded successfully', 'success');
    } catch (error) {
        console.error('Export failed:', error);
        Utils.notify('Export failed', 'error');
    }
}

/**
 * Copy table to clipboard
 */
function copyTableToClipboard() {
    const table = document.querySelector('.results-table');
    if (!table) return;

    const range = document.createRange();
    range.selectNodeContents(table);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    try {
        document.execCommand('copy');
        Utils.notify('Table copied to clipboard', 'success');
    } catch {
        Utils.notify('Failed to copy to clipboard', 'error');
    }

    selection.removeAllRanges();
}

/**
 * Print results
 */
function printResults() {
    window.print();
}

/**
 * Render result row with details
 */
function renderResultRow(result) {
    const truncatedUrl = Utils.truncate(result.url, 60);
    return `
        <tr onclick="toggleRowDetails(this)">
            <td><a href="${result.url}" target="_blank" title="${result.url}">${truncatedUrl}</a></td>
            <td>${result.total_matches}</td>
            <td><span class="status-badge">Match</span></td>
        </tr>
        <tr class="details-row" style="display: none;">
            <td colspan="3">
                <div style="padding: 20px; background: #f9f9f9; border-radius: 4px;">
                    <p><strong>Full URL:</strong> <code style="word-break: break-all;">${result.url}</code></p>
                    ${result.sample_match ? `<p><strong>Sample Match:</strong><br><code style="display: block; background: #f0f0f0; padding: 10px; margin-top: 5px; overflow-x: auto;">${escapeHtml(result.sample_match.substring(0, 200))}</code></p>` : ''}
                    <p style="margin-top: 10px; font-size: 12px; color: #666;">Click row to toggle details</p>
                </div>
            </td>
        </tr>
    `;
}

/**
 * Toggle row details
 */
function toggleRowDetails(row) {
    const nextRow = row.nextElementSibling;
    if (nextRow && nextRow.classList.contains('details-row')) {
        nextRow.style.display = nextRow.style.display === 'none' ? 'table-row' : 'none';
    }
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Setup advanced filters
 */
function setupAdvancedFilters() {
    const filterBtn = document.getElementById('filter-btn');
    const filterPanel = document.getElementById('filter-panel');

    if (filterBtn && filterPanel) {
        filterBtn.addEventListener('click', () => {
            filterPanel.style.display = filterPanel.style.display === 'none' ? 'block' : 'none';
        });
    }
}

/**
 * Apply advanced filters
 */
function applyAdvancedFilters() {
    // This would be implemented based on specific filter requirements
    loadResults(1);
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+E for export
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            document.getElementById('export-btn')?.click();
        }

        // Ctrl+F for search (allow default)
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            printResults();
        }
    });
}

/**
 * Initialize page
 */
function initResultsPage() {
    setupAdvancedFilters();
    setupKeyboardShortcuts();

    // Add export menu
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            const menu = document.getElementById('export-menu');
            if (!menu) {
                const menuHtml = `
                    <div id="export-menu" style="position: absolute; top: 100%; right: 0; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 100;">
                        <button onclick="handleExport('json')" class="btn-link" style="display: block; width: 100%; text-align: left; padding: 10px 15px; border: none; background: none; cursor: pointer;">
                            Export as JSON
                        </button>
                        <button onclick="handleExport('csv')" class="btn-link" style="display: block; width: 100%; text-align: left; padding: 10px 15px; border: none; background: none; cursor: pointer; border-top: 1px solid #eee;">
                            Export as CSV
                        </button>
                        <button onclick="handleExport('html')" class="btn-link" style="display: block; width: 100%; text-align: left; padding: 10px 15px; border: none; background: none; cursor: pointer; border-top: 1px solid #eee;">
                            Export as HTML
                        </button>
                        <button onclick="copyTableToClipboard()" class="btn-link" style="display: block; width: 100%; text-align: left; padding: 10px 15px; border: none; background: none; cursor: pointer; border-top: 1px solid #eee;">
                            Copy to Clipboard
                        </button>
                        <button onclick="printResults()" class="btn-link" style="display: block; width: 100%; text-align: left; padding: 10px 15px; border: none; background: none; cursor: pointer; border-top: 1px solid #eee;">
                            Print
                        </button>
                    </div>
                `;

                const container = document.createElement('div');
                container.style.position = 'relative';
                container.style.display = 'inline-block';
                exportBtn.parentNode.insertBefore(container, exportBtn);
                container.appendChild(exportBtn);
                container.innerHTML += menuHtml;
            }

            const menu = document.getElementById('export-menu');
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        });
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', initResultsPage);
