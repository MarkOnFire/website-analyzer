/**
 * Settings Page Script
 *
 * Handles:
 * - Application settings management
 * - Theme preferences
 * - Display options
 * - System information
 */

/**
 * Load settings
 */
function loadSettings() {
    // Load from localStorage
    const theme = localStorage.getItem('bug-finder-theme') || 'auto';
    const itemsPerPage = localStorage.getItem('items-per-page') || '20';
    const maxPages = localStorage.getItem('max-pages') || '1000';
    const timeout = localStorage.getItem('timeout') || '30';

    document.getElementById('theme-setting').value = theme;
    document.getElementById('items-per-page').value = itemsPerPage;
    document.getElementById('max-pages').value = maxPages;
    document.getElementById('timeout').value = timeout;
}

/**
 * Save settings
 */
function saveSettings() {
    const theme = document.getElementById('theme-setting').value;
    const itemsPerPage = document.getElementById('items-per-page').value;
    const maxPages = document.getElementById('max-pages').value;
    const timeout = document.getElementById('timeout').value;

    // Validate
    if (itemsPerPage < 5 || itemsPerPage > 100) {
        Utils.notify('Items per page must be between 5 and 100', 'warning');
        return;
    }

    if (maxPages < 10 || maxPages > 10000) {
        Utils.notify('Max pages must be between 10 and 10000', 'warning');
        return;
    }

    if (timeout < 5 || timeout > 300) {
        Utils.notify('Timeout must be between 5 and 300 seconds', 'warning');
        return;
    }

    // Save
    localStorage.setItem('bug-finder-theme', theme);
    localStorage.setItem('items-per-page', itemsPerPage);
    localStorage.setItem('max-pages', maxPages);
    localStorage.setItem('timeout', timeout);

    // Apply theme
    ThemeManager.apply(theme);

    Utils.notify('Settings saved successfully', 'success');
    document.getElementById('settings-message').innerHTML =
        '<p style="color: #4CAF50; margin-top: 10px;">Settings saved successfully!</p>';

    setTimeout(() => {
        document.getElementById('settings-message').innerHTML = '';
    }, 3000);
}

/**
 * Load system information
 */
async function loadSystemInfo() {
    const container = document.getElementById('system-info');
    if (!container) return;

    try {
        const health = await API.health();

        const info = `
            <div class="info-box">
                <p><strong>Status:</strong> ${health.status}</p>
                <p><strong>Base Directory:</strong> <code>${health.base_dir}</code></p>
                <p><strong>Current Time:</strong> ${new Date(health.timestamp).toLocaleString()}</p>
            </div>

            <div class="info-box">
                <p><strong>Browser:</strong> ${getBrowserInfo()}</p>
                <p><strong>Platform:</strong> ${navigator.platform}</p>
                <p><strong>JavaScript Enabled:</strong> Yes</p>
                <p><strong>Local Storage:</strong> ${isLocalStorageAvailable() ? 'Available' : 'Not available'}</p>
            </div>

            <div class="info-box">
                <h4 style="margin-bottom: 10px;">Keyboard Shortcuts</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px; font-weight: 500;">Shortcut</td>
                        <td style="padding: 8px; font-weight: 500;">Action</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px;"><code>Ctrl+Enter</code></td>
                        <td style="padding: 8px;">Submit form (on patterns page)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px;"><code>Ctrl+K</code></td>
                        <td style="padding: 8px;">Focus search (future)</td>
                    </tr>
                </table>
            </div>
        `;

        container.innerHTML = info;
    } catch (error) {
        console.error('Failed to load system info:', error);
        container.innerHTML = '<p style="color: #f44336;">Failed to load system information</p>';
    }
}

/**
 * Get browser info
 */
function getBrowserInfo() {
    const ua = navigator.userAgent;
    let browser = 'Unknown';

    if (ua.indexOf('Chrome') > -1) browser = 'Chrome';
    else if (ua.indexOf('Safari') > -1) browser = 'Safari';
    else if (ua.indexOf('Firefox') > -1) browser = 'Firefox';
    else if (ua.indexOf('Edge') > -1) browser = 'Edge';

    return browser;
}

/**
 * Check if local storage is available
 */
function isLocalStorageAvailable() {
    try {
        const test = '__localStorage_test__';
        localStorage.setItem(test, test);
        localStorage.removeItem(test);
        return true;
    } catch {
        return false;
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    const saveBtn = document.getElementById('save-settings');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveSettings);
    }

    // Allow Enter to save
    const inputs = ['theme-setting', 'items-per-page', 'max-pages', 'timeout'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el && el.tagName === 'INPUT') {
            el.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    saveSettings();
                }
            });
        }
    });
}

/**
 * Initialize page
 */
function initPage() {
    loadSettings();
    loadSystemInfo();
    setupEventListeners();
}

// Load on page ready
document.addEventListener('DOMContentLoaded', initPage);
