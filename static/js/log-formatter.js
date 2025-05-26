/**
 * Log Formatter Module
 * Provides formatting functionality for log messages in the UI
 */

const LogFormatter = {
    /**
     * Format a log message for display
     * @param {string} content - The raw log content
     * @returns {object} - Formatted content and metadata
     */
    formatLogMessage: function(content) {
        // Try to detect the type of log message
        const logType = this.detectLogType(content);
        
        // Format based on type
        let formattedContent;
        switch (logType) {
            case 'json':
                formattedContent = this.formatJSON(content);
                break;
            case 'error':
                formattedContent = this.formatError(content);
                break;
            case 'tool_use':
                formattedContent = this.formatToolUse(content);
                break;
            case 'result':
                formattedContent = this.formatResult(content);
                break;
            default:
                formattedContent = this.formatPlain(content);
        }
        
        return {
            type: logType,
            formatted: formattedContent,
            collapsible: this.shouldBeCollapsible(content)
        };
    },
    
    /**
     * Detect the type of log message
     */
    detectLogType: function(content) {
        // Check for JSON
        if (this.isJSON(content)) {
            return 'json';
        }
        
        // Check for tool use patterns
        if (content.includes('Using tool:') || content.includes('Tool:')) {
            return 'tool_use';
        }
        
        // Check for result patterns
        if (content.includes('Result from') || content.includes('TextContent(')) {
            return 'result';
        }
        
        // Check for error patterns
        if (content.toLowerCase().includes('error') || content.toLowerCase().includes('exception')) {
            return 'error';
        }
        
        return 'plain';
    },
    
    /**
     * Check if a string is valid JSON
     */
    isJSON: function(str) {
        try {
            JSON.parse(str);
            return true;
        } catch (e) {
            // Check if it's a JSON-like structure within a larger string
            return /\{[\s\S]*\}|\[[\s\S]*\]/.test(str);
        }
    },
    
    /**
     * Format JSON content
     */
    formatJSON: function(content) {
        try {
            // Try to parse as pure JSON
            const parsed = JSON.parse(content);
            return this.createJSONElement(parsed);
        } catch (e) {
            // Try to extract JSON from the content
            const jsonMatch = content.match(/(\{[\s\S]*\}|\[[\s\S]*\])/);
            if (jsonMatch) {
                try {
                    const parsed = JSON.parse(jsonMatch[1]);
                    const prefix = content.substring(0, jsonMatch.index);
                    const suffix = content.substring(jsonMatch.index + jsonMatch[1].length);
                    
                    return `${this.escapeHtml(prefix)}${this.createJSONElement(parsed)}${this.escapeHtml(suffix)}`;
                } catch (e2) {
                    // If parsing fails, format as plain text
                    return this.formatPlain(content);
                }
            }
            return this.formatPlain(content);
        }
    },
    
    /**
     * Create formatted JSON HTML element
     */
    createJSONElement: function(obj) {
        const jsonString = JSON.stringify(obj, null, 2);
        const highlighted = this.highlightJSON(jsonString);
        return `<pre class="json-content">${highlighted}</pre>`;
    },
    
    /**
     * Highlight JSON syntax
     */
    highlightJSON: function(json) {
        // Replace special characters
        json = this.escapeHtml(json);
        
        // Highlight different JSON elements
        json = json.replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:');
        json = json.replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>');
        json = json.replace(/: (\d+)/g, ': <span class="json-number">$1</span>');
        json = json.replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>');
        json = json.replace(/: (null)/g, ': <span class="json-null">$1</span>');
        
        return json;
    },
    
    /**
     * Format tool use messages
     */
    formatToolUse: function(content) {
        const lines = content.split('\n');
        let formatted = '<div class="tool-use-log">';
        
        lines.forEach(line => {
            if (line.includes('Using tool:') || line.includes('Tool:')) {
                const toolName = line.split(':')[1]?.trim() || '';
                formatted += `<div class="tool-header"><i class="fas fa-wrench"></i> ${this.escapeHtml(line)}</div>`;
            } else if (line.trim()) {
                formatted += `<div class="tool-params">${this.escapeHtml(line)}</div>`;
            }
        });
        
        formatted += '</div>';
        return formatted;
    },
    
    /**
     * Format result messages
     */
    formatResult: function(content) {
        // Check for TextContent pattern
        if (content.includes('TextContent(')) {
            return this.formatTextContent(content);
        }
        
        // Check for "Result from" pattern
        if (content.includes('Result from')) {
            const parts = content.split(':');
            const header = parts[0];
            const body = parts.slice(1).join(':');
            
            return `<div class="result-log">
                <div class="result-header"><i class="fas fa-check-circle"></i> ${this.escapeHtml(header)}</div>
                <div class="result-body">${this.formatJSON(body)}</div>
            </div>`;
        }
        
        return this.formatPlain(content);
    },
    
    /**
     * Format TextContent messages
     */
    formatTextContent: function(content) {
        // Extract the JSON part from TextContent
        const match = content.match(/TextContent\(type='text', text='(.*)'\)/);
        if (match) {
            try {
                // The text content is a JSON string
                const jsonStr = match[1].replace(/\\'/g, "'").replace(/\\"/g, '"').replace(/\\\\/g, '\\');
                const parsed = JSON.parse(jsonStr);
                
                return `<div class="result-log">
                    <div class="result-header"><i class="fas fa-file-alt"></i> File Content Result</div>
                    <div class="result-body">${this.createJSONElement(parsed)}</div>
                </div>`;
            } catch (e) {
                return this.formatPlain(content);
            }
        }
        
        return this.formatPlain(content);
    },
    
    /**
     * Format error messages
     */
    formatError: function(content) {
        return `<div class="error-log">
            <div class="error-header"><i class="fas fa-exclamation-triangle"></i> Error</div>
            <div class="error-body">${this.escapeHtml(content)}</div>
        </div>`;
    },
    
    /**
     * Format plain text
     */
    formatPlain: function(content) {
        return `<div class="plain-log">${this.escapeHtml(content)}</div>`;
    },
    
    /**
     * Determine if content should be collapsible
     */
    shouldBeCollapsible: function(content) {
        // Make collapsible if more than 5 lines or 500 characters
        const lineCount = content.split('\n').length;
        return lineCount > 5 || content.length > 500;
    },
    
    /**
     * Escape HTML special characters
     */
    escapeHtml: function(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },
    
    /**
     * Create a collapsible log element
     */
    createCollapsibleLog: function(content, isCollapsed = false) {
        const id = 'log-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const preview = content.substring(0, 100) + (content.length > 100 ? '...' : '');
        
        return `
            <div class="collapsible-log ${isCollapsed ? 'collapsed' : ''}" id="${id}">
                <div class="log-toggle" onclick="LogFormatter.toggleLog('${id}')">
                    <i class="fas fa-chevron-${isCollapsed ? 'right' : 'down'}"></i>
                    <span class="log-preview">${this.escapeHtml(preview)}</span>
                </div>
                <div class="log-full-content" style="display: ${isCollapsed ? 'none' : 'block'}">
                    ${content}
                </div>
            </div>
        `;
    },
    
    /**
     * Toggle a collapsible log
     */
    toggleLog: function(id) {
        const element = document.getElementById(id);
        if (!element) return;
        
        const isCollapsed = element.classList.contains('collapsed');
        const toggle = element.querySelector('.log-toggle i');
        const content = element.querySelector('.log-full-content');
        
        if (isCollapsed) {
            element.classList.remove('collapsed');
            toggle.className = 'fas fa-chevron-down';
            content.style.display = 'block';
        } else {
            element.classList.add('collapsed');
            toggle.className = 'fas fa-chevron-right';
            content.style.display = 'none';
        }
    }
};

// Make LogFormatter available globally
window.LogFormatter = LogFormatter;