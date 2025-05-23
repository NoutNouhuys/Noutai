// Main JavaScript file for the Anthropic Console

document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    initThemeToggle();
    
    // Login button functionality
    const loginButton = document.querySelector('.btn-login');
    if (loginButton) {
        loginButton.addEventListener('click', function(e) {
            // Let the link handle the redirect (already points to auth.login route)
            // We're not preventing default behavior here to allow redirect
        });
    }
    
    // Initialize chat interface (if user is logged in)
    const chatMessages = document.getElementById('chat-messages');
    const promptInput = document.getElementById('prompt-input');
    const sendPromptButton = document.getElementById('send-prompt');
    const modelSelect = document.getElementById('model-select');
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // State variables for conversation
    let currentConversationId = null;
    let isWaitingForResponse = false;
    
    // Load available models for the dropdown if it exists
    if (modelSelect) {
        loadAvailableModels();
    }
    
    if (chatMessages && promptInput && sendPromptButton) {
        // Create a new conversation when the chat interface loads
        createNewConversation();
        
        // Set up event listeners for chat
        sendPromptButton.addEventListener('click', function() {
            sendPrompt();
        });
        
        promptInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendPrompt();
            }
        });
        
        // Add welcome message to the chat
        addSystemMessage('Welkom bij de Lynxx Anthropic Console. Wat kan ik voor je doen?');
    }
    
    // Keyboard shortcut for theme toggle (Alt+T)
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 't') {
            const toggleSwitch = document.getElementById('theme-toggle');
            if (toggleSwitch) {
                toggleSwitch.checked = !toggleSwitch.checked;
                
                // Trigger the change event to apply theme
                const event = new Event('change');
                toggleSwitch.dispatchEvent(event);
            }
        }
    });
    
    // Theme Toggle functionality
    function initThemeToggle() {
        const toggleSwitch = document.getElementById('theme-toggle');
        const themeIcon = document.querySelector('.theme-icon i');
        
        // Function to set theme based on preference
        const setTheme = (themeName) => {
            document.documentElement.setAttribute('data-theme', themeName);
            localStorage.setItem('theme', themeName);
            
            if (toggleSwitch) {
                toggleSwitch.checked = themeName === 'dark';
            }
            
            if (themeIcon) {
                themeIcon.className = themeName === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
            
            // Re-apply syntax highlighting for proper theme colors
            if (typeof Prism !== 'undefined') {
                Prism.highlightAll();
            }
        };
        
        // Check for saved user preference first
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            // Apply saved theme
            setTheme(savedTheme);
        } else {
            // Check for system preference if no saved preference
            const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(prefersDarkScheme ? 'dark' : 'light');
        }
        
        // Listen for toggle changes
        if (toggleSwitch) {
            toggleSwitch.addEventListener('change', function(e) {
                const newTheme = e.target.checked ? 'dark' : 'light';
                setTheme(newTheme);
            });
        }
        
        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            // Only automatically change theme if user hasn't set a preference
            if (!localStorage.getItem('theme')) {
                const newTheme = e.matches ? 'dark' : 'light';
                setTheme(newTheme);
            }
        });
    }
    
    // Function to create a new conversation
    function createNewConversation() {
        fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentConversationId = data.conversation.id;
                console.log('Nieuwe conversatie gestart: ' + currentConversationId);
            } else {
                console.error('Kon geen nieuwe conversatie starten:', data.error);
            }
        })
        .catch(error => {
            console.error('Error bij het maken van een nieuwe conversatie:', error);
        });
    }
    
    // Function to load available models
    function loadAvailableModels(selectEl = modelSelect) {
        if (!selectEl) {
            return;
        }

        fetch('/api/models')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.models) {
                // Clear existing options
                selectEl.innerHTML = '';

                // Add models to dropdown
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = `${model.name} - ${model.description}`;
                    selectEl.appendChild(option);
                });
            } else {
                console.error('Kon modellen niet laden:', data.error);
            }
        })
        .catch(error => {
            console.error('Error bij het laden van modellen:', error);
        });
    }
    
    // Function to send prompt to Claude
    function sendPrompt() {
        const prompt = promptInput.value.trim();
        
        if (prompt && !isWaitingForResponse) {
            // Get selected model
            const selectedModel = modelSelect ? modelSelect.value : 'claude-3-haiku-20240307';
            
            // Add user message to chat
            addUserMessage(prompt);
            
            // Clear input
            promptInput.value = '';
            
            // Show loading indicator
            isWaitingForResponse = true;
            addLoadingIndicator();
            
            const params = new URLSearchParams({
                prompt: prompt,
                model_id: selectedModel,
                conversation_id: currentConversationId || ''
            });

            const es = new EventSource('/api/prompt_stream?' + params.toString());

            es.addEventListener('log', function(e) {
                const msg = JSON.parse(e.data);
                addLogMessage(msg);
            });

            es.addEventListener('final', function(e) {
                const data = JSON.parse(e.data);
                removeLoadingIndicator();
                isWaitingForResponse = false;

                if (data.success) {
                    addSystemMessage(data.message);
                    if (data.conversation_id && !currentConversationId) {
                        currentConversationId = data.conversation_id;
                    }
                } else {
                    addErrorMessage(data.error || 'Er ging iets mis bij het verwerken van je verzoek.');
                }
                es.close();
            });

            es.addEventListener('error', function(err) {
                removeLoadingIndicator();
                isWaitingForResponse = false;
                addErrorMessage('Er ging iets mis bij het versturen van je bericht.');
                console.error('Error bij het versturen van prompt:', err);
                es.close();
            });
        }
    }
    
    // Function to add user message to chat
    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to add system message to chat
    function addSystemMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        
        // Enable markdown formatting with syntax highlighting
        const formattedMessage = formatMessage(message);
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${formattedMessage}
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Apply syntax highlighting to all code blocks in this message
        highlightCodeBlocks(messageDiv);
    }

    // Function to add log message to chat
    function addLogMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message log';

        const formattedMessage = formatMessage(message);
        messageDiv.innerHTML = `
            <div class="message-content">
                ${formattedMessage}
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        highlightCodeBlocks(messageDiv);
    }
    
    // Function to add error message
    function addErrorMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message error-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to add loading indicator
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message system-message loading';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="message-content">
                <div class="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                </div>
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to remove loading indicator
    function removeLoadingIndicator() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }
    
    // Function to format message with markdown and syntax highlighting
    function formatMessage(message) {
        // Escape HTML first
        let formattedMessage = escapeHtml(message);
        
        // Convert code blocks with language specification ```language code ``` to HTML with appropriate classes
        formattedMessage = formattedMessage.replace(/```([a-zA-Z0-9_]+)?\\s*\\n([\\s\\S]*?)```/g, (match, language, code) => {
            const lang = language || 'plaintext';
            return `<pre><code class="language-${lang}">${code}</code></pre>`;
        });
        
        // Convert code blocks without language specification
        formattedMessage = formattedMessage.replace(/```([\\s\\S]*?)```/g, (match, code) => {
            return `<pre><code class="language-plaintext">${code}</code></pre>`;
        });
        
        // Convert inline code `code` to HTML
        formattedMessage = formattedMessage.replace(/`([^`]+)`/g, '<code class="language-plaintext">$1</code>');
        
        // Convert paragraphs (double newlines)
        formattedMessage = formattedMessage.replace(/\\n\\n/g, '</p><p>');
        
        // Convert newlines to <br>
        formattedMessage = formattedMessage.replace(/\\n/g, '<br>');
        
        // Wrap in paragraph tags
        formattedMessage = `<p>${formattedMessage}</p>`;
        
        return formattedMessage;
    }
    
    // Function to apply syntax highlighting to code blocks
    function highlightCodeBlocks(container) {
        // Check if Prism is available
        if (typeof Prism !== 'undefined') {
            // Find all code elements in the container and apply highlighting
            Prism.highlightAllUnder(container);
        }
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
    
    // Handle auto-hiding of flash messages
    const flashMessages = document.querySelectorAll('.message:not(.user-message):not(.system-message):not(.error-message)');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.style.display = 'none';
                }, 500);
            });
        }, 5000);
    }
});
