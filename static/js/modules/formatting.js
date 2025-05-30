// Message formatting and display module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

AIOntwikkelhulp.Formatting = (function() {
    
    // Public API
    return {
        formatMessage: formatMessage,
        escapeHtml: escapeHtml,
        addMessageToChat: addMessageToChat,
        addLogMessage: addLogMessage,
        addLoadingMessage: addLoadingMessage,
        removeLoadingMessage: removeLoadingMessage,
        addErrorMessage: addErrorMessage
    };
    
    // Function to format message with markdown and syntax highlighting
    function formatMessage(message) {
        // Escape HTML first
        let formattedMessage = escapeHtml(message);
        
        // Convert code blocks with language specification ```language code ``` to HTML with appropriate classes
        formattedMessage = formattedMessage.replace(/```([a-zA-Z0-9_]+)?\s*\n([\s\S]*?)```/g, (match, language, code) => {
            const lang = language || 'plaintext';
            return `<pre><code class="language-${lang}">${code}</code></pre>`;
        });
        
        // Convert code blocks without language specification
        formattedMessage = formattedMessage.replace(/```([\s\S]*?)```/g, (match, code) => {
            return `<pre><code class="language-plaintext">${code}</code></pre>`;
        });
        
        // Convert inline code `code` to HTML
        formattedMessage = formattedMessage.replace(/`([^`]+)`/g, '<code class="language-plaintext">$1</code>');
        
        // Convert paragraphs (double newlines)
        formattedMessage = formattedMessage.replace(/\n\n/g, '</p><p>');
        
        // Convert newlines to <br>
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');
        
        // Wrap in paragraph tags
        formattedMessage = `<p>${formattedMessage}</p>`;
        
        return formattedMessage;
    }
    
    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    function addMessageToChat(windowId, role, content) {
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const chatMessages = windowElement.querySelector('.chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const iconSpan = document.createElement('div');
        iconSpan.className = 'message-icon';
        
        if (role === 'user') {
            iconSpan.innerHTML = '<i class="fas fa-user me-1"></i> Jij';
        } else if (role === 'assistant') {
            iconSpan.innerHTML = '<i class="fas fa-robot me-1"></i> Claude';
        } else {
            iconSpan.innerHTML = '<i class="fas fa-info-circle me-1"></i> Systeem';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Apply markdown and code formatting
        contentDiv.innerHTML = formatMessage(content);
        
        messageDiv.appendChild(iconSpan);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Apply syntax highlighting to code blocks if Prism is available
        if (typeof Prism !== 'undefined') {
            Prism.highlightAllUnder(messageDiv);
        }
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addLogMessage(windowId, content) {
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const logMessages = windowElement.querySelector('.log-messages');
        
        // Format the log message using LogFormatter
        const formattedLog = LogFormatter.formatLogMessage(content);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'log-message';

        const timestamp = new Date().toLocaleTimeString();
        const timeSpan = document.createElement('span');
        timeSpan.className = 'log-timestamp';
        timeSpan.textContent = timestamp;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'log-content';
        
        // Use formatted content instead of plain text
        if (formattedLog.collapsible) {
            contentDiv.innerHTML = LogFormatter.createCollapsibleLog(formattedLog.formatted, true);
        } else {
            contentDiv.innerHTML = formattedLog.formatted;
        }
        
        messageDiv.appendChild(timeSpan);
        messageDiv.appendChild(contentDiv);
        logMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        logMessages.scrollTop = logMessages.scrollHeight;
    }
    
    function addLoadingMessage(windowId, loadingId) {
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const chatMessages = windowElement.querySelector('.chat-messages');
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant loading';
        loadingDiv.id = loadingId;
        
        const iconSpan = document.createElement('div');
        iconSpan.className = 'message-icon';
        iconSpan.innerHTML = '<i class="fas fa-robot me-1"></i> Claude';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        
        loadingDiv.appendChild(iconSpan);
        loadingDiv.appendChild(contentDiv);
        chatMessages.appendChild(loadingDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function removeLoadingMessage(windowId, loadingId) {
        const loadingMessage = document.getElementById(loadingId);
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }
    
    function addErrorMessage(windowId, errorText) {
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const chatMessages = windowElement.querySelector('.chat-messages');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message error';
        
        const iconSpan = document.createElement('div');
        iconSpan.className = 'message-icon';
        iconSpan.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Foutmelding';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = errorText;
        
        errorDiv.appendChild(iconSpan);
        errorDiv.appendChild(contentDiv);
        chatMessages.appendChild(errorDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
})();