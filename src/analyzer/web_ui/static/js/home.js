/**
 * Home Page Script
 *
 * Handles:
 * - Loading and displaying recent scans
 * - Loading and displaying projects
 * - Quick navigation and stats
 */

let scansData = [];
let projectsData = [];

/**
 * Load recent scans
 */
async function loadScans() {
    const container = document.getElementById('scans-list');
    if (!container) return;

    try {
        const data = await API.getScans({ limit: 10 });
        scansData = data.scans || [];

        if (scansData.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; padding: 40px;">No scans yet. Start a scan from the CLI to see results here.</p>';
            return;
        }

        container.innerHTML = scansData.map(scan => `
            <div class="scan-card" onclick="window.location.href = '/scan/${scan.id}'">
                <div class="card-title">${Utils.truncate(scan.site_url, 40)}</div>
                <div class="card-subtitle">${Utils.formatDate(scan.created_at)}</div>
                <div class="info-box" style="margin: 10px 0;">
                    <p><strong>Status:</strong> <span class="status-badge status-${scan.status}">${scan.status}</span></p>
                    <p><strong>Bugs Found:</strong> ${scan.bug_count}</p>
                    <p><strong>Pages:</strong> ${scan.pages_scanned}</p>
                </div>
                <button class="btn btn-primary" onclick="event.stopPropagation(); window.location.href = '/scan/${scan.id}'">View Results</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load scans:', error);
        container.innerHTML = '<p style="grid-column: 1/-1; color: #f44336;">Failed to load scans</p>';
    }
}

/**
 * Load projects
 */
async function loadProjects() {
    const container = document.getElementById('projects-list');
    if (!container) return;

    try {
        const data = await API.getProjects();
        projectsData = data.projects || [];

        if (projectsData.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 40px;">No projects yet. Create a project from the CLI to see it here.</p>';
            return;
        }

        container.innerHTML = '<table class="results-table"><thead><tr><th>Project</th><th>URL</th><th>Created</th><th>Last Scan</th><th>Action</th></tr></thead><tbody>' +
            projectsData.map(project => `
                <tr>
                    <td><strong>${project.slug}</strong></td>
                    <td><a href="${project.url}" target="_blank">${Utils.truncate(project.url, 50)}</a></td>
                    <td>${Utils.formatDateShort(project.created_at)}</td>
                    <td>${project.last_scan ? Utils.formatDateShort(project.last_scan) : '-'}</td>
                    <td><a href="/project/${project.slug}" class="btn-link">View</a></td>
                </tr>
            `).join('') +
            '</tbody></table>';
    } catch (error) {
        console.error('Failed to load projects:', error);
        container.innerHTML = '<p style="color: #f44336;">Failed to load projects</p>';
    }
}

/**
 * Initialize page
 */
async function initPage() {
    await loadScans();
    await loadProjects();
}

// Load on page ready
document.addEventListener('DOMContentLoaded', initPage);

// Refresh every 30 seconds
setInterval(initPage, 30000);
