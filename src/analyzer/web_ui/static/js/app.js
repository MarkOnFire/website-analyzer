/**
 * Bug Finder Dashboard - Main Application Script
 *
 * Handles global functionality:
 * - Theme switching (light/dark mode)
 * - API communication
 * - Utility functions
 */

// =============================================================================
// Theme Management
// =============================================================================

const ThemeManager = {
    STORAGE_KEY: 'bug-finder-theme',
    LIGHT: 'light',
    DARK: 'dark',
    AUTO: 'auto',

    /**
     * Initialize theme manager and apply saved theme
     */
    init() {
        const btn = document.getElementById('theme-btn');
        if (btn) {
            btn.addEventListener('click', () => this.toggle());
        }

        // Apply saved theme or system preference
        const saved = localStorage.getItem(this.STORAGE_KEY) || this.AUTO;
        this.apply(saved);
    },

    /**
     * Get current theme
     */
    get() {
        const saved = localStorage.getItem(this.STORAGE_KEY) || this.AUTO;
        if (saved === this.AUTO) {
            return this.getSystemTheme();
        }
        return saved;
    },

    /**
     * Get system preferred theme
     */
    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? this.DARK : this.LIGHT;
    },

    /**
     * Apply theme
     */
    apply(theme) {
        const isDark = theme === this.DARK ||
            (theme === this.AUTO && this.getSystemTheme() === this.DARK);

        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            this.updateButton('☀️');
        } else {
            document.documentElement.removeAttribute('data-theme');
            this.updateButton('🌙');
        }

        localStorage.setItem(this.STORAGE_KEY, theme);
    },

    /**
     * Toggle between light and dark theme
     */
    toggle() {
        const current = this.get();
        const next = current === this.LIGHT ? this.DARK : this.LIGHT;
        this.apply(next);
    },

    /**
     * Update theme button text
     */
    updateButton(emoji) {
        const btn = document.getElementById('theme-btn');
        if (btn) {
            btn.textContent = emoji;
        }
    }
};

// =============================================================================
// API Client
// =============================================================================

const API = {
    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * Get projects
     */
    async getProjects() {
        return this.request('/api/projects');
    },

    /**
     * Get project by slug
     */
    async getProject(slug) {
        return this.request(`/api/projects/${slug}`);
    },

    /**
     * Get scans
     */
    async getScans(options = {}) {
        const params = new URLSearchParams();
        if (options.limit) params.append('limit', options.limit);
        if (options.status) params.append('status', options.status);
        if (options.project_slug) params.append('project_slug', options.project_slug);

        const url = `/api/scans${params.toString() ? '?' + params : ''}`;
        return this.request(url);
    },

    /**
     * Get scan by ID
     */
    async getScan(scanId) {
        return this.request(`/api/scans/${scanId}`);
    },

    /**
     * Get scan results with pagination
     */
    async getScanResults(scanId, options = {}) {
        const params = new URLSearchParams();
        if (options.page) params.append('page', options.page);
        if (options.per_page) params.append('per_page', options.per_page);
        if (options.search) params.append('search', options.search);
        if (options.sort_by) params.append('sort_by', options.sort_by);
        if (options.sort_order) params.append('sort_order', options.sort_order);

        const url = `/api/scans/${scanId}/results${params.toString() ? '?' + params : ''}`;
        return this.request(url);
    },

    /**
     * Get scan statistics
     */
    async getScanStats(scanId) {
        return this.request(`/api/scans/${scanId}/stats`);
    },

    /**
     * Get patterns
     */
    async getPatterns() {
        return this.request('/api/patterns');
    },

    /**
     * Get pattern by name
     */
    async getPattern(name) {
        return this.request(`/api/patterns/${name}`);
    },

    /**
     * Health check
     */
    async health() {
        return this.request('/api/health');
    }
};

// =============================================================================
// Utility Functions
// =============================================================================

const Utils = {
    /**
     * Format date/time
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    },

    /**
     * Format short date
     */
    formatDateShort(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    },

    /**
     * Format duration from start date
     */
    formatDuration(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate || new Date());
        const seconds = Math.floor((end - start) / 1000);

        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        return `${Math.floor(seconds / 3600)}h`;
    },

    /**
     * Truncate string
     */
    truncate(str, length = 50) {
        if (str.length <= length) return str;
        return str.substring(0, length) + '...';
    },

    /**
     * Format URL for display
     */
    formatUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname + urlObj.pathname;
        } catch {
            return url;
        }
    },

    /**
     * Generate color for status
     */
    getStatusColor(status) {
        const colors = {
            'completed': '#4CAF50',
            'completed_clean': '#2196F3',
            'running': '#ff9800',
            'error': '#f44336',
            'pending': '#9E9E9E',
        };
        return colors[status] || '#999';
    },

    /**
     * Show notification
     */
    notify(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            background-color: ${this.getNotificationColor(type)};
            color: white;
            z-index: 10000;
            animation: slideIn 0.3s ease-in;
        `;

        document.body.appendChild(notification);

        if (duration) {
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }

        return notification;
    },

    /**
     * Get notification color
     */
    getNotificationColor(type) {
        const colors = {
            'success': '#4CAF50',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196F3',
        };
        return colors[type] || '#666';
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Copy to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.notify('Copied to clipboard', 'success', 2000);
            return true;
        } catch {
            return false;
        }
    }
};

// Add global CSS animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// =============================================================================
// Initialize on Load
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();

    // Verify API is accessible
    API.health()
        .then(() => console.log('Dashboard initialized'))
        .catch(() => console.warn('API health check failed'));
});
