/**
 * FirstVerify Dynamic Reporting Engine - Frontend Application
 * Main application logic for report generation and management
 */

class ReportingApp {
    constructor() {
        this.selectedQuestions = new Set();
        this.reportData = null;
        this.currentPage = 1;
        this.pageSize = 10;
        this.isLoading = false;
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.setupEventListeners();
        await this.loadMetadata();
        this.renderQuestions();
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Sidebar controls
        document.getElementById('selectAllBtn')?.addEventListener('click', () => this.selectAll());
        document.getElementById('clearAllBtn')?.addEventListener('click', () => this.clearAll());

        // Report generation
        document.getElementById('generateBtn')?.addEventListener('click', () => this.generateReport());

        // Export functionality
        document.getElementById('exportBtn')?.addEventListener('click', () => this.exportToExcel());

        // Pagination
        document.getElementById('prevPageBtn')?.addEventListener('click', () => this.previousPage());
        document.getElementById('nextPageBtn')?.addEventListener('click', () => this.nextPage());
        document.getElementById('pageSizeSelect')?.addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.currentPage = 1;
            this.renderTable();
        });

        // Health check on load
        this.checkHealth();
    }

    /**
     * Check API health
     */
    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();
            if (health.status !== 'healthy') {
                this.showAlert('⚠️ Database connection issue. Some features may not work.', 'warning');
            }
        } catch (error) {
            this.showAlert('⚠️ Cannot connect to API server.', 'warning');
        }
    }

    /**
     * Load metadata (available questions) from API
     */
    async loadMetadata() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/metadata');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            this.questions = data.questions || [];
            console.log(`Loaded ${this.questions.length} questions`);
        } catch (error) {
            console.error('Error loading metadata:', error);
            this.showAlert(`Error loading questions: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Render question checkboxes in sidebar
     */
    renderQuestions() {
        const container = document.getElementById('questionsContainer');
        if (!container) return;

        container.innerHTML = '';

        if (!this.questions || this.questions.length === 0) {
            container.innerHTML = '<p class="text-muted">No questions available</p>';
            return;
        }

        this.questions.forEach((question, index) => {
            const checkbox = document.createElement('div');
            checkbox.className = 'form-check';
            checkbox.innerHTML = `
                <input 
                    type="checkbox" 
                    class="question-checkbox" 
                    id="question-${index}"
                    data-question="${question}"
                    ${this.selectedQuestions.has(question) ? 'checked' : ''}
                >
                <label for="question-${index}" title="${question}">
                    ${this.truncateText(question, 45)}
                </label>
            `;

            checkbox.querySelector('input').addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedQuestions.add(question);
                } else {
                    this.selectedQuestions.delete(question);
                }
                this.updateSelectedCount();
            });

            container.appendChild(checkbox);
        });

        this.updateSelectedCount();
    }

    /**
     * Update the selected questions count display
     */
    updateSelectedCount() {
        const countDisplay = document.getElementById('selectedCount');
        if (countDisplay) {
            countDisplay.textContent = this.selectedQuestions.size;
        }

        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.disabled = this.selectedQuestions.size === 0;
        }
    }

    /**
     * Select all questions
     */
    selectAll() {
        this.questions.forEach(question => this.selectedQuestions.add(question));
        document.querySelectorAll('.question-checkbox').forEach(cb => cb.checked = true);
        this.updateSelectedCount();
    }

    /**
     * Clear all selections
     */
    clearAll() {
        this.selectedQuestions.clear();
        document.querySelectorAll('.question-checkbox').forEach(cb => cb.checked = false);
        this.updateSelectedCount();
    }

    /**
     * Generate report based on selected questions
     */
    async generateReport() {
        if (this.selectedQuestions.size === 0) {
            this.showAlert('Please select at least one question', 'warning');
            return;
        }

        try {
            this.isLoading = true;
            this.showLoading(true);
            this.currentPage = 1;

            const response = await fetch('/api/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_questions: Array.from(this.selectedQuestions)
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            this.reportData = await response.json();
            console.log(`Report generated: ${this.reportData.total_rows} rows`);

            this.renderTable();
            this.showAlert(`✓ Report generated successfully with ${this.reportData.total_rows} rows`, 'success');

            // Show export button
            const exportBtn = document.getElementById('exportBtn');
            if (exportBtn) exportBtn.classList.remove('hidden');

        } catch (error) {
            console.error('Error generating report:', error);
            this.showAlert(`Error generating report: ${error.message}`, 'error');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    /**
     * Render the report table with pagination
     */
    renderTable() {
        const container = document.getElementById('tableContainer');
        if (!container) return;

        if (!this.reportData || this.reportData.rows.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📊</div>
                    <h3>No Data</h3>
                    <p>Generate a report to view results</p>
                </div>
            `;
            this.updatePagination();
            return;
        }

        // Calculate pagination
        const totalPages = Math.ceil(this.reportData.total_rows / this.pageSize);
        if (this.currentPage > totalPages && totalPages > 0) {
            this.currentPage = totalPages;
        }

        const startIndex = (this.currentPage - 1) * this.pageSize;
        const endIndex = Math.min(startIndex + this.pageSize, this.reportData.rows.length);
        const paginatedRows = this.reportData.rows.slice(startIndex, endIndex);

        // Build table HTML
        let html = '<div class="table-container"><div class="table-wrapper"><table class="report-table"><thead><tr>';

        // Table headers with aliases
        this.reportData.columns.forEach(column => {
            const alias = this.reportData.column_aliases[column] || column;
            html += `<th title="${column}">${this.escapeHtml(alias)}</th>`;
        });
        html += '</tr></thead><tbody>';

        // Table rows
        paginatedRows.forEach(row => {
            html += '<tr>';
            this.reportData.columns.forEach(column => {
                const value = row[column] ?? '';
                const isNumeric = typeof value === 'number' || !isNaN(parseFloat(value));
                const cellClass = isNumeric ? 'numeric' : '';
                html += `<td class="${cellClass}">${this.escapeHtml(String(value))}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div></div>';
        container.innerHTML = html;
        this.updatePagination();
    }

    /**
     * Update pagination controls
     */
    updatePagination() {
        const totalPages = this.reportData ? Math.ceil(this.reportData.total_rows / this.pageSize) : 0;
        const infoText = this.reportData
            ? `Page ${this.currentPage} of ${totalPages} (${this.reportData.total_rows} total rows)`
            : '';

        const infoEl = document.getElementById('paginationInfo');
        if (infoEl) infoEl.textContent = infoText;

        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');

        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
    }

    /**
     * Go to previous page
     */
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderTable();
        }
    }

    /**
     * Go to next page
     */
    nextPage() {
        const totalPages = Math.ceil(this.reportData.total_rows / this.pageSize);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderTable();
        }
    }

    /**
     * Export report data to Excel
     */
    exportToExcel() {
        if (!this.reportData || this.reportData.rows.length === 0) {
            this.showAlert('No data to export', 'warning');
            return;
        }

        try {
            // Prepare data for Excel
            const headers = this.reportData.columns.map(col =>
                this.reportData.column_aliases[col] || col
            );
            const data = [headers];

            this.reportData.rows.forEach(row => {
                const rowData = this.reportData.columns.map(col => row[col] ?? '');
                data.push(rowData);
            });

            // Create workbook
            const ws = XLSX.utils.aoa_to_sheet(data);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Report");

            // Auto-fit columns
            const colWidths = headers.map((_, i) => {
                const maxLength = Math.max(
                    headers[i].length,
                    ...this.reportData.rows.map(row => String(row[this.reportData.columns[i]] ?? '').length)
                );
                return { wch: Math.min(maxLength + 2, 50) };
            });
            ws['!cols'] = colWidths;

            // Generate filename with timestamp
            const timestamp = new Date().toISOString().slice(0, 10);
            const filename = `FirstVerify_Report_${timestamp}.xlsx`;

            // Write file
            XLSX.writeFile(wb, filename);
            this.showAlert(`✓ Report exported as ${filename}`, 'success');

        } catch (error) {
            console.error('Error exporting to Excel:', error);
            this.showAlert(`Error exporting: ${error.message}`, 'error');
        }
    }

    /**
     * Show loading indicator
     */
    showLoading(show = true) {
        const loader = document.getElementById('loadingIndicator');
        if (loader) {
            loader.classList.toggle('hidden', !show);
        }
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const container = document.getElementById('alertContainer');
        if (!container) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `<span>${message}</span>`;

        container.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => alert.remove(), 5000);
    }

    /**
     * Truncate text to specified length
     */
    truncateText(text, length) {
        return text.length > length ? text.substring(0, length) + '...' : text;
    }

    /**
     * Escape HTML special characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ReportingApp();
});
