/**
 * Patterns Page Script
 *
 * Handles:
 * - Loading and displaying patterns
 * - Pattern testing interface
 */

let patternsData = [];

/**
 * Load patterns list
 */
async function loadPatterns() {
    const container = document.getElementById('patterns-list');
    const select = document.getElementById('pattern-select');

    if (!container && !select) return;

    try {
        const data = await API.getPatterns();
        patternsData = data.patterns || [];

        // Update list container
        if (container) {
            if (patternsData.length === 0) {
                container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 40px;">No patterns available. Create patterns from the CLI.</p>';
            } else {
                container.innerHTML = patternsData.map(pattern => `
                    <div class="pattern-card" onclick="selectPattern('${pattern.name || pattern.filename}')">
                        <div class="card-title">${pattern.name || pattern.filename}</div>
                        <div class="card-subtitle">${pattern.description || 'No description'}</div>
                        ${pattern.severity ? `<p><strong>Severity:</strong> <span style="color: ${getSeverityColor(pattern.severity)}">${pattern.severity}</span></p>` : ''}
                        ${pattern.patterns_count ? `<p><strong>Patterns:</strong> ${pattern.patterns_count}</p>` : ''}
                        ${pattern.tags && pattern.tags.length > 0 ? `<p><strong>Tags:</strong> ${pattern.tags.slice(0, 3).join(', ')}${pattern.tags.length > 3 ? '...' : ''}</p>` : ''}
                        <button class="btn btn-primary" onclick="event.stopPropagation(); selectPattern('${pattern.name || pattern.filename}')">Test</button>
                    </div>
                `).join('');
            }
        }

        // Update select dropdown
        if (select) {
            select.innerHTML = '<option value="">-- Select a pattern --</option>' +
                patternsData.map(pattern => `
                    <option value="${pattern.name || pattern.filename}">${pattern.name || pattern.filename}</option>
                `).join('');
        }
    } catch (error) {
        console.error('Failed to load patterns:', error);
        if (container) {
            container.innerHTML = '<p style="grid-column: 1/-1; color: #f44336;">Failed to load patterns</p>';
        }
    }
}

/**
 * Select pattern for testing
 */
function selectPattern(patternName) {
    const select = document.getElementById('pattern-select');
    if (select) {
        select.value = patternName;
    }
    // Scroll to test section
    const testSection = document.querySelector('.section:has(#test-content)');
    if (testSection) {
        testSection.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Get severity color
 */
function getSeverityColor(severity) {
    const colors = {
        'low': '#FFC107',
        'medium': '#FF9800',
        'high': '#F44336',
        'critical': '#B71C1C',
    };
    return colors[severity] || '#999';
}

/**
 * Test pattern
 */
async function testPattern() {
    const patternName = document.getElementById('pattern-select').value;
    const content = document.getElementById('test-content').value;
    const resultsDiv = document.getElementById('test-results');

    if (!patternName) {
        Utils.notify('Please select a pattern', 'warning');
        return;
    }

    if (!content) {
        Utils.notify('Please enter content to test', 'warning');
        return;
    }

    try {
        resultsDiv.innerHTML = '<div class="loading">Testing pattern...</div>';

        // This would typically call an API endpoint to test the pattern
        // For now, we'll show a message that this requires backend implementation
        resultsDiv.innerHTML = `
            <div class="info-box">
                <p><strong>Pattern:</strong> ${patternName}</p>
                <p><strong>Content Length:</strong> ${content.length} characters</p>
                <p style="margin-top: 10px; color: #666; font-size: 14px;">
                    Pattern testing against custom content requires connecting to the pattern library API.
                    Run the CLI command to test patterns:
                </p>
                <code style="display: block; background: #f5f5f5; padding: 10px; margin-top: 10px; border-radius: 4px; overflow-x: auto;">
                    python -m src.analyzer.cli bug-finder patterns test --pattern ${patternName} --content "..."
                </code>
            </div>
        `;
    } catch (error) {
        console.error('Failed to test pattern:', error);
        resultsDiv.innerHTML = '<p style="color: #f44336;">Failed to test pattern</p>';
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    const testBtn = document.getElementById('test-btn');
    if (testBtn) {
        testBtn.addEventListener('click', testPattern);
    }

    const patternSelect = document.getElementById('pattern-select');
    if (patternSelect) {
        patternSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                document.getElementById('test-content').focus();
            }
        });
    }

    // Allow Ctrl+Enter to test
    const testContent = document.getElementById('test-content');
    if (testContent) {
        testContent.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                testPattern();
            }
        });
    }
}

/**
 * Initialize page
 */
async function initPage() {
    await loadPatterns();
    setupEventListeners();
}

// Load on page ready
document.addEventListener('DOMContentLoaded', initPage);
