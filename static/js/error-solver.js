/**
 * Error Solver Frontend Module
 * 
 * Provides frontend functionality for the error solving feature.
 * Handles error analysis, solution generation, and user interface interactions.
 */

class ErrorSolver {
    constructor() {
        this.currentTempPath = null;
        this.analysisResults = null;
        this.solutionResults = null;
        this.isAnalyzing = false;
        this.isSolving = false;
        
        this.initializeEventListeners();
        this.initializeFileUpload();
    }
    
    /**
     * Initialize event listeners for the error solver interface
     */
    initializeEventListeners() {
        // Error analysis form submission
        const analyzeForm = document.getElementById('error-analyze-form');
        if (analyzeForm) {
            analyzeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.analyzeError();
            });
        }
        
        // Solution generation button
        const solveButton = document.getElementById('generate-solutions-btn');
        if (solveButton) {
            solveButton.addEventListener('click', () => {
                this.generateSolutions();
            });
        }
        
        // Repository upload form
        const uploadForm = document.getElementById('repo-upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.uploadRepository();
            });
        }
        
        // Clear results button
        const clearButton = document.getElementById('clear-results-btn');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearResults();
            });
        }
        
        // Copy code buttons (delegated event handling)
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('copy-code-btn')) {
                this.copyCodeToClipboard(e.target);
            }
        });
        
        // Expand/collapse sections
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('section-toggle')) {
                this.toggleSection(e.target);
            }
        });
    }
    
    /**
     * Initialize file upload functionality
     */
    initializeFileUpload() {
        const fileInput = document.getElementById('repo-file-input');
        const dropZone = document.getElementById('repo-drop-zone');
        
        if (fileInput && dropZone) {
            // File input change
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
            });
            
            // Drag and drop
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                this.handleFileSelection(e.dataTransfer.files);
            });
            
            // Click to select file
            dropZone.addEventListener('click', () => {
                fileInput.click();
            });
        }
    }
    
    /**
     * Handle file selection for repository upload
     */
    handleFileSelection(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.name.toLowerCase().endsWith('.zip')) {
                document.getElementById('selected-file-name').textContent = file.name;
                document.getElementById('upload-repo-btn').disabled = false;
            } else {
                this.showError('Please select a ZIP file containing your repository.');
            }
        }
    }
    
    /**
     * Upload repository for analysis
     */
    async uploadRepository() {
        const fileInput = document.getElementById('repo-file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a repository file to upload.');
            return;
        }
        
        const uploadBtn = document.getElementById('upload-repo-btn');
        const originalText = uploadBtn.textContent;
        
        try {
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
            
            const formData = new FormData();
            formData.append('repo_file', file);
            
            const response = await fetch('/api/error/upload-repo', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentTempPath = result.temp_path;
                document.getElementById('repo-path-input').value = result.temp_path;
                this.showSuccess(`Repository uploaded successfully! Found ${result.file_count} files.`);
                
                // Enable analysis form
                document.getElementById('error-analyze-form').style.display = 'block';
            } else {
                this.showError(result.error || 'Failed to upload repository');
            }
            
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = originalText;
        }
    }
    
    /**
     * Analyze error in the repository
     */
    async analyzeError() {
        if (this.isAnalyzing) return;
        
        const repoPath = document.getElementById('repo-path-input').value.trim();
        const errorMessage = document.getElementById('error-message-input').value.trim();
        const errorType = document.getElementById('error-type-select').value;
        
        if (!repoPath) {
            this.showError('Please provide a repository path or upload a repository.');
            return;
        }
        
        if (!errorMessage) {
            this.showError('Please provide an error message to analyze.');
            return;
        }
        
        this.isAnalyzing = true;
        const analyzeBtn = document.querySelector('#error-analyze-form button[type=\"submit\"]');
        const originalText = analyzeBtn.textContent;
        
        try {
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = 'Analyzing...';
            
            this.showLoading('Analyzing error...');
            
            const response = await fetch('/api/error/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    repo_path: repoPath,
                    error_message: errorMessage,
                    error_type: errorType || null
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.analysisResults = result;
                this.displayAnalysisResults(result);
                this.showSuccess('Error analysis completed successfully!');
                
                // Enable solution generation
                document.getElementById('generate-solutions-btn').disabled = false;
            } else {
                this.showError(result.error || 'Error analysis failed');
            }
            
        } catch (error) {
            this.showError('Analysis failed: ' + error.message);
        } finally {
            this.isAnalyzing = false;
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = originalText;
            this.hideLoading();
        }
    }
    
    /**
     * Generate solutions for the analyzed error
     */
    async generateSolutions() {
        if (this.isSolving || !this.analysisResults) return;
        
        const repoPath = document.getElementById('repo-path-input').value.trim();
        const errorMessage = document.getElementById('error-message-input').value.trim();
        const errorType = document.getElementById('error-type-select').value;
        
        this.isSolving = true;
        const solveBtn = document.getElementById('generate-solutions-btn');
        const originalText = solveBtn.textContent;
        
        try {
            solveBtn.disabled = true;
            solveBtn.textContent = 'Generating Solutions...';
            
            this.showLoading('Generating AI-powered solutions...');
            
            const response = await fetch('/api/error/solve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    repo_path: repoPath,
                    error_message: errorMessage,
                    error_type: errorType || null,
                    include_code_fixes: true,
                    include_explanations: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.solutionResults = result;
                this.displaySolutionResults(result);
                this.showSuccess('Solutions generated successfully!');
            } else {
                this.showError(result.error || 'Solution generation failed');
            }
            
        } catch (error) {
            this.showError('Solution generation failed: ' + error.message);
        } finally {
            this.isSolving = false;
            solveBtn.disabled = false;
            solveBtn.textContent = originalText;
            this.hideLoading();
        }
    }
    
    /**
     * Display error analysis results
     */
    displayAnalysisResults(results) {
        const container = document.getElementById('analysis-results');
        if (!container) return;
        
        container.innerHTML = '';
        container.style.display = 'block';
        
        // Error classification
        const classification = results.classification || {};
        const classificationHtml = `
            <div class="result-section">
                <h3 class="section-title">
                    <span class="section-toggle" data-target="classification-content">📊 Error Classification</span>
                </h3>
                <div id="classification-content" class="section-content">
                    <div class="classification-grid">
                        <div class="classification-item">
                            <strong>Type:</strong> ${classification.primary_type || 'Unknown'}
                        </div>
                        <div class="classification-item">
                            <strong>Language:</strong> ${classification.language || 'Unknown'}
                        </div>
                        <div class="classification-item">
                            <strong>Category:</strong> ${classification.category || 'Unknown'}
                        </div>
                        <div class="classification-item">
                            <strong>Severity:</strong> 
                            <span class="severity-badge severity-${results.severity || 'medium'}">${results.severity || 'Medium'}</span>
                        </div>
                    </div>
                    ${classification.secondary_types && classification.secondary_types.length > 0 ? `
                        <div class="secondary-types">
                            <strong>Secondary Types:</strong> ${classification.secondary_types.join(', ')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Error locations
        const locations = results.locations || [];
        const locationsHtml = locations.length > 0 ? `
            <div class="result-section">
                <h3 class="section-title">
                    <span class="section-toggle" data-target="locations-content">📍 Error Locations</span>
                </h3>
                <div id="locations-content" class="section-content">
                    ${locations.map((location, index) => `
                        <div class="location-item">
                            <h4>📁 ${location.relative_path || location.file_path}</h4>
                            <div class="file-info">
                                <span class="file-type">${location.file_type}</span>
                                <span class="line-count">${location.total_lines} lines</span>
                            </div>
                            ${location.matches && location.matches.length > 0 ? `
                                <div class="matches">
                                    ${location.matches.map(match => `
                                        <div class="match-item">
                                            <div class="match-header">
                                                <span class="line-number">Line ${match.line_number}</span>
                                                <span class="match-type">${match.match_type}</span>
                                                <span class="confidence">Confidence: ${Math.round((match.confidence || 0) * 100)}%</span>
                                            </div>
                                            <pre class="code-snippet"><code>${this.escapeHtml(match.line_content)}</code></pre>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : '';
        
        // Code context
        const context = results.context || [];
        const contextHtml = context.length > 0 ? `
            <div class="result-section">
                <h3 class="section-title">
                    <span class="section-toggle" data-target="context-content">🔍 Code Context</span>
                </h3>
                <div id="context-content" class="section-content">
                    ${context.map((ctx, index) => `
                        <div class="context-item">
                            <h4>📄 ${ctx.relative_path || ctx.file_path}</h4>
                            <div class="context-info">
                                <span>Error on line ${ctx.error_line}</span>
                                <span>Context: lines ${ctx.context_start}-${ctx.context_end}</span>
                            </div>
                            <div class="code-context">
                                <pre class="code-block"><code>${ctx.context_lines.map(line => 
                                    `<span class="line-number ${line.is_error_line ? 'error-line' : ''}">${line.line_number.toString().padStart(3, ' ')}</span><span class="line-content ${line.is_error_line ? 'error-line' : ''}">${this.escapeHtml(line.content)}</span>`
                                ).join('\n')}</code></pre>
                                <button class="copy-code-btn" data-code="${this.escapeHtml(ctx.context_lines.map(l => l.content).join('\n'))}">
                                    📋 Copy Code
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : '';
        
        // Basic suggestions
        const suggestions = results.suggestions || [];
        const suggestionsHtml = suggestions.length > 0 ? `
            <div class="result-section">
                <h3 class="section-title">
                    <span class="section-toggle" data-target="suggestions-content">💡 Basic Suggestions</span>
                </h3>
                <div id="suggestions-content" class="section-content">
                    <ul class="suggestions-list">
                        ${suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                    </ul>
                </div>
            </div>
        ` : '';
        
        container.innerHTML = classificationHtml + locationsHtml + contextHtml + suggestionsHtml;
    }
    
    /**
     * Display solution results
     */
    displaySolutionResults(results) {
        const container = document.getElementById('solution-results');
        if (!container) return;
        
        container.innerHTML = '';
        container.style.display = 'block';
        
        const aiSolutions = results.ai_solutions || {};
        const templateSolutions = results.template_solutions || {};
        const recommendedActions = results.recommended_actions || [];
        const preventionTips = results.prevention_tips || [];
        const resources = results.resources || [];
        
        let html = '';
        
        // AI Solutions
        if (aiSolutions.success && aiSolutions.parsed_solutions) {
            const parsed = aiSolutions.parsed_solutions;
            html += `
                <div class="result-section">
                    <h3 class="section-title">
                        <span class="section-toggle" data-target="ai-solutions-content">🤖 AI-Generated Solutions</span>
                    </h3>
                    <div id="ai-solutions-content" class="section-content">
                        ${parsed.root_cause ? `
                            <div class="solution-subsection">
                                <h4>🔍 Root Cause Analysis</h4>
                                <div class="solution-text">${this.formatText(parsed.root_cause)}</div>
                            </div>
                        ` : ''}
                        
                        ${parsed.impact_assessment ? `
                            <div class="solution-subsection">
                                <h4>📊 Impact Assessment</h4>
                                <div class="solution-text">${this.formatText(parsed.impact_assessment)}</div>
                            </div>
                        ` : ''}
                        
                        ${parsed.code_fixes && parsed.code_fixes.length > 0 ? `
                            <div class="solution-subsection">
                                <h4>🔧 Code Fixes</h4>
                                <div class="solution-text">${this.formatText(parsed.code_fixes.join('\n'))}</div>
                            </div>
                        ` : ''}
                        
                        ${parsed.step_by_step && parsed.step_by_step.length > 0 ? `
                            <div class="solution-subsection">
                                <h4>📋 Step-by-Step Solution</h4>
                                <ol class="step-list">
                                    ${parsed.step_by_step.map(step => `<li>${step}</li>`).join('')}
                                </ol>
                            </div>
                        ` : ''}
                        
                        <div class="ai-info">
                            <small>Generated using ${aiSolutions.model_used} • ${aiSolutions.token_count || 0} tokens</small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Template Solutions
        if (templateSolutions.common_fixes) {
            html += `
                <div class="result-section">
                    <h3 class="section-title">
                        <span class="section-toggle" data-target="template-solutions-content">📋 Quick Fixes</span>
                    </h3>
                    <div id="template-solutions-content" class="section-content">
                        <div class="priority-badge priority-${templateSolutions.priority}">${templateSolutions.priority.toUpperCase()}</div>
                        <ul class="quick-fixes-list">
                            ${templateSolutions.common_fixes.map(fix => `<li>${fix}</li>`).join('')}
                        </ul>
                        
                        ${templateSolutions.quick_checks && templateSolutions.quick_checks.length > 0 ? `
                            <div class="solution-subsection">
                                <h4>⚡ Quick Checks</h4>
                                <ul class="quick-checks-list">
                                    ${templateSolutions.quick_checks.map(check => `<li>${check}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        // Recommended Actions
        if (recommendedActions.length > 0) {
            html += `
                <div class="result-section">
                    <h3 class="section-title">
                        <span class="section-toggle" data-target="actions-content">🎯 Recommended Actions</span>
                    </h3>
                    <div id="actions-content" class="section-content">
                        <div class="actions-grid">
                            ${recommendedActions.map(action => `
                                <div class="action-item priority-${action.priority}">
                                    <div class="action-header">
                                        <span class="action-title">${action.action}</span>
                                        <span class="priority-badge">${action.priority}</span>
                                    </div>
                                    <div class="action-description">${action.description}</div>
                                    <div class="action-time">⏱️ ${action.estimated_time}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Prevention Tips
        if (preventionTips.length > 0) {
            html += `
                <div class="result-section">
                    <h3 class="section-title">
                        <span class="section-toggle" data-target="prevention-content">🛡️ Prevention Tips</span>
                    </h3>
                    <div id="prevention-content" class="section-content">
                        <ul class="prevention-list">
                            ${preventionTips.map(tip => `<li>${tip}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
        
        // Helpful Resources
        if (resources.length > 0) {
            html += `
                <div class="result-section">
                    <h3 class="section-title">
                        <span class="section-toggle" data-target="resources-content">📚 Helpful Resources</span>
                    </h3>
                    <div id="resources-content" class="section-content">
                        <div class="resources-grid">
                            ${resources.map(resource => `
                                <div class="resource-item">
                                    <h4><a href="${resource.url}" target="_blank" rel="noopener">${resource.title}</a></h4>
                                    <p>${resource.description}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }
    
    /**
     * Clear all results and reset the interface
     */
    clearResults() {
        // Clear results containers
        const analysisResults = document.getElementById('analysis-results');
        const solutionResults = document.getElementById('solution-results');
        
        if (analysisResults) {
            analysisResults.innerHTML = '';
            analysisResults.style.display = 'none';
        }
        
        if (solutionResults) {
            solutionResults.innerHTML = '';
            solutionResults.style.display = 'none';
        }
        
        // Reset form
        const form = document.getElementById('error-analyze-form');
        if (form) {
            form.reset();
        }
        
        // Reset file upload
        const fileInput = document.getElementById('repo-file-input');
        if (fileInput) {
            fileInput.value = '';
        }
        
        const fileName = document.getElementById('selected-file-name');
        if (fileName) {
            fileName.textContent = 'No file selected';
        }
        
        // Disable buttons
        document.getElementById('generate-solutions-btn').disabled = true;
        document.getElementById('upload-repo-btn').disabled = true;
        
        // Clean up temporary files
        if (this.currentTempPath) {
            this.cleanupTempFiles();
        }
        
        // Reset state
        this.analysisResults = null;
        this.solutionResults = null;
        this.currentTempPath = null;
        
        this.showSuccess('Results cleared successfully!');
    }
    
    /**
     * Clean up temporary repository files
     */
    async cleanupTempFiles() {
        if (!this.currentTempPath) return;
        
        try {
            await fetch('/api/error/cleanup-temp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    temp_path: this.currentTempPath
                })
            });
        } catch (error) {
            console.warn('Failed to cleanup temp files:', error);
        }
    }
    
    /**
     * Copy code to clipboard
     */
    async copyCodeToClipboard(button) {
        const code = button.getAttribute('data-code');
        
        try {
            await navigator.clipboard.writeText(code);
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        } catch (error) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = code;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            button.textContent = '✅ Copied!';
            setTimeout(() => {
                button.textContent = '📋 Copy Code';
            }, 2000);
        }
    }
    
    /**
     * Toggle section visibility
     */
    toggleSection(toggleElement) {
        const targetId = toggleElement.getAttribute('data-target');
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            const isVisible = targetElement.style.display !== 'none';
            targetElement.style.display = isVisible ? 'none' : 'block';
            
            // Update toggle indicator
            const indicator = toggleElement.textContent.charAt(0);
            toggleElement.textContent = toggleElement.textContent.replace(indicator, isVisible ? '▶️' : '🔽');
        }
    }
    
    /**
     * Show loading indicator
     */
    showLoading(message) {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.textContent = message;
            loadingDiv.style.display = 'block';
        }
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    /**
     * Show error message
     */
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    /**
     * Show message with specified type
     */
    showMessage(message, type) {
        const messageDiv = document.getElementById('message-container');
        if (messageDiv) {
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = message;
            messageDiv.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    }
    
    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Format text with basic markdown-like formatting
     */
    formatText(text) {
        if (!text) return '';
        
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
}

// Initialize error solver when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('error-solver-container')) {
        window.errorSolver = new ErrorSolver();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorSolver;
}