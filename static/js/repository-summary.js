/**
 * Repository Summary Generator JavaScript
 * 
 * Provides functionality for generating and managing repository summaries
 * through the web interface.
 */

class RepositorySummaryManager {
    constructor() {
        this.apiBaseUrl = '/api/repository/summary';
        this.isGenerating = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkExistingSummary();
    }

    bindEvents() {
        // Generate summary button
        const generateBtn = document.getElementById('generate-summary-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateSummary());
        }

        // Refresh summary button
        const refreshBtn = document.getElementById('refresh-summary-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadExistingSummary());
        }

        // Download summary button
        const downloadBtn = document.getElementById('download-summary-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadSummary());
        }
    }

    async checkExistingSummary() {
        try {
            const response = await fetch(this.apiBaseUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.displaySummary(data.content);
                    this.showSummaryActions();
                } else {
                    this.showGenerateOption();
                }
            } else {
                this.showGenerateOption();
            }
        } catch (error) {
            console.error('Error checking existing summary:', error);
            this.showGenerateOption();
        }
    }

    async loadExistingSummary() {
        try {
            this.showLoading('Loading existing summary...');

            const response = await fetch(this.apiBaseUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.displaySummary(data.content);
                this.showSummaryActions();
                this.showSuccess('Summary loaded successfully');
            } else {
                this.showError(data.error || 'Failed to load summary');
                this.showGenerateOption();
            }
        } catch (error) {
            console.error('Error loading summary:', error);
            this.showError('Failed to load summary');
        } finally {
            this.hideLoading();
        }
    }

    async generateSummary(forceOverwrite = false) {
        if (this.isGenerating) {
            return;
        }

        try {
            this.isGenerating = true;
            this.showLoading('Generating repository summary... This may take a few moments.');

            const requestBody = {
                repo_path: '.',
                output_filename: 'repository_summary.txt',
                force_overwrite: forceOverwrite
            };

            const response = await fetch(this.apiBaseUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(`Repository summary generated successfully! File size: ${this.formatFileSize(data.file_size)}`);
                this.displaySummary(data.summary_preview);
                this.showSummaryActions();
                
                // Load the full summary
                setTimeout(() => this.loadExistingSummary(), 1000);
            } else {
                if (data.file_exists && !forceOverwrite) {
                    this.showOverwriteConfirmation();
                } else {
                    this.showError(data.error || 'Failed to generate summary');
                }
            }
        } catch (error) {
            console.error('Error generating summary:', error);
            this.showError('Failed to generate summary');
        } finally {
            this.isGenerating = false;
            this.hideLoading();
        }
    }

    showOverwriteConfirmation() {
        const confirmed = confirm(
            'A repository summary file already exists. Do you want to overwrite it?'
        );
        
        if (confirmed) {
            this.generateSummary(true);
        }
    }

    displaySummary(content) {
        const summaryContainer = document.getElementById('summary-content');
        if (summaryContainer) {
            // Convert markdown to HTML for better display
            summaryContainer.innerHTML = this.markdownToHtml(content);
            summaryContainer.style.display = 'block';
        }

        const noSummaryMessage = document.getElementById('no-summary-message');
        if (noSummaryMessage) {
            noSummaryMessage.style.display = 'none';
        }
    }

    showGenerateOption() {
        const generateSection = document.getElementById('generate-section');
        if (generateSection) {
            generateSection.style.display = 'block';
        }

        const summaryContainer = document.getElementById('summary-content');
        if (summaryContainer) {
            summaryContainer.style.display = 'none';
        }

        const noSummaryMessage = document.getElementById('no-summary-message');
        if (noSummaryMessage) {
            noSummaryMessage.style.display = 'block';
        }
    }

    showSummaryActions() {
        const actionsSection = document.getElementById('summary-actions');
        if (actionsSection) {
            actionsSection.style.display = 'block';
        }

        const generateSection = document.getElementById('generate-section');
        if (generateSection) {
            generateSection.style.display = 'none';
        }
    }

    async downloadSummary() {
        try {
            const response = await fetch(this.apiBaseUrl, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.downloadFile(data.content, 'repository_summary.txt', 'text/plain');
                } else {
                    this.showError('Failed to download summary');
                }
            } else {
                this.showError('Failed to download summary');
            }
        } catch (error) {
            console.error('Error downloading summary:', error);
            this.showError('Failed to download summary');
        }
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    markdownToHtml(markdown) {
        // Simple markdown to HTML conversion
        let html = markdown
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^\* (.*$)/gim, '<li>$1</li>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*)\*/gim, '<em>$1</em>')
            .replace(/```([\\s\\S]*?)```/gim, '<pre><code>$1</code></pre>')
            .replace(/`([^`]*)`/gim, '<code>$1</code>')
            .replace(/\\n/gim, '<br>');

        // Wrap consecutive <li> elements in <ul>
        html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');
        
        return html;
    }

    showLoading(message) {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.textContent = message;
            loadingElement.style.display = 'block';
        }

        // Disable generate button
        const generateBtn = document.getElementById('generate-summary-btn');
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        }
    }

    hideLoading() {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        // Re-enable generate button
        const generateBtn = document.getElementById('generate-summary-btn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Summary';
        }
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        // Create or update message element
        let messageElement = document.getElementById('summary-message');
        if (!messageElement) {
            messageElement = document.createElement('div');
            messageElement.id = 'summary-message';
            messageElement.className = 'alert';
            
            const container = document.getElementById('summary-container') || document.body;
            container.insertBefore(messageElement, container.firstChild);
        }

        messageElement.className = `alert alert-${type === 'error' ? 'danger' : 'success'}`;
        messageElement.textContent = message;
        messageElement.style.display = 'block';

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('repository-summary-section')) {
        new RepositorySummaryManager();
    }
});