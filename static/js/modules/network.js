// Backend communication module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

AIOntwikkelhulp.Network = (function() {
    
    // Public API
    return {
        getCSRFToken: getCSRFToken,
        getAPIHeaders: getAPIHeaders,
        sendPrompt: sendPrompt,
        sendPromptWithConfig: sendPromptWithConfig,
        sendPromptWithRetry: sendPromptWithRetry,
        populateModelSelect: populateModelSelect,
        populatePresetSelect: populatePresetSelect,
        loadConversation: loadConversation,
        resetConversation: resetConversation,
        fetchLastAssistantMessage: fetchLastAssistantMessage,
        updateMcpStatus: updateMcpStatus
    };
    
    // Get CSRF token from meta tag
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }

    // Create headers with CSRF token for API requests
    function getAPIHeaders(includeContentType = true) {
        const headers = {
            'X-CSRFToken': getCSRFToken()
        };
        
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        
        return headers;
    }
    
    function fetchLastAssistantMessage() {
        return new Promise((resolve, reject) => {
            const lastConversationId = AIOntwikkelhulp.State.getLastConversationId();

            if (!lastConversationId) {
                reject("No conversation ID provided.");
                return;
            }

            fetch(`/api/conversations/${lastConversationId}/last_message`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    console.log('Parsing JSON response');
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.last_message) {
                        resolve(data.last_message);
                    } else {
                        reject("No assistant response found.");
                    }
                })
                .catch(error => {
                    console.error('Error fetching last message:', error);
                    reject(error);
                });
        });
    }

    function populateModelSelect(selectEl) {
        if (!selectEl) return;

        fetch('/api/models')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.models) {
                    selectEl.innerHTML = '';
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

    function populatePresetSelect(selectEl) {
        if (!selectEl) return;

        fetch('/api/llm-settings/presets')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.presets) {
                    // Cache presets for later use
                    AIOntwikkelhulp.State.setAvailablePresets(data.presets);
                    
                    // Clear existing options except the default one
                    selectEl.innerHTML = '<option value="">Standaard</option>';
                    
                    // Add preset options
                    Object.keys(data.presets).forEach(presetName => {
                        const preset = data.presets[presetName];
                        const option = document.createElement('option');
                        option.value = preset.id;
                        option.textContent = preset.name || presetName;
                        option.title = preset.description || `Temperature: ${preset.temperature}`;
                        selectEl.appendChild(option);
                    });
                } else {
                    console.error('Kon presets niet laden:', data.error);
                }
            })
            .catch(error => {
                console.error('Error bij het laden van presets:', error);
            });
    }

    // Function to update MCP server status in the UI
    function updateMcpStatus(activeServers) {
        let statusBar = document.getElementById("mcp-status-bar");
        let mcpList = document.getElementById("mcp-servers-list");

        if (activeServers && activeServers.length > 0) {
            mcpList.textContent = activeServers.join(", ");
            statusBar.classList.remove("d-none");
        } else {
            mcpList.textContent = "Geen";
            statusBar.classList.add("d-none");
        }
    }
    
    function loadConversation(windowId, conversationId) {
        const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
        if (!windowData) return;
        
        windowData.conversationId = conversationId;

        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const statusElement = windowElement.querySelector('.conversation-status');
        
        statusElement.textContent = 'Gesprek laden...';
        
        fetch(`/api/conversations/${conversationId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const { conversation, messages } = data.data;
                    
                    // Update conversation status
                    statusElement.textContent = `Gesprek: ${conversation.title}`;
                    
                    // Select the model that was used in this conversation
                    const modelSelect = windowElement.querySelector('.model-select');
                    if (conversation.model) {
                        for (let i = 0; i < modelSelect.options.length; i++) {
                            if (modelSelect.options[i].value === conversation.model) {
                                modelSelect.selectedIndex = i;
                                break;
                            }
                        }
                    }
                    
                    // Clear chat and log messages
                    const chatMessages = windowElement.querySelector('.chat-messages');
                    const logMessages = windowElement.querySelector('.log-messages');
                    chatMessages.innerHTML = '';
                    logMessages.innerHTML = '';
                    
                    // Populate messages in the appropriate columns
                    messages.forEach(message => {
                        if (message.role === 'log') {
                            AIOntwikkelhulp.Formatting.addLogMessage(windowId, message.content);
                        } else {
                            AIOntwikkelhulp.Formatting.addMessageToChat(windowId, message.role, message.content);
                        }
                    });
                    
                    // Scroll to bottom
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    logMessages.scrollTop = logMessages.scrollHeight;
                } else {
                    console.error('Error loading conversation:', data.error);
                    statusElement.textContent = 'Fout bij laden gesprek';
                }
            })
            .catch(error => {
                console.error('Error loading conversation:', error);
                statusElement.textContent = 'Fout bij laden gesprek';
            });
    }

    function resetConversation(windowId) {
        const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
        if (!windowData) return;

        windowData.conversationId = null;
        windowData.workflowConfig = null;

        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const chatMessages = windowElement.querySelector('.chat-messages');
        const logMessages = windowElement.querySelector('.log-messages');
        const statusElement = windowElement.querySelector('.conversation-status');
        const promptInput = windowElement.querySelector('.prompt-input');

        // Clear both chat and log messages
        chatMessages.innerHTML = '';
        logMessages.innerHTML = '';
        statusElement.textContent = 'Nieuw gesprek';

        // Focus on the input
        promptInput.focus();
    }
    
    // New function to send prompt with specific model and preset configuration
    function sendPromptWithConfig(windowId, prompt, modelId, presetName) {
        const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
        if (!windowData || windowData.isWaitingForResponse) return;
        
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        
        if (!prompt || prompt.trim() === '') {
            return;
        }
        
        // Add user message to chat
        AIOntwikkelhulp.Formatting.addMessageToChat(windowId, 'user', prompt);
        
        // Add loading indicator
        const loadingId = 'loading-' + Date.now();
        AIOntwikkelhulp.Formatting.addLoadingMessage(windowId, loadingId);
        
        console.log(`[Send Config] Sending prompt with configured model: ${modelId}, preset: ${presetName || 'none'}`);
        
        // Set waiting flag
        windowData.isWaitingForResponse = true;
        
        // Prepare request with specific model and preset
        const requestData = {
            prompt: prompt,
            model_id: modelId,
            preset_name: presetName || undefined
        };
        
        // Add conversation_id if continuing a conversation
        if (windowData.conversationId) {
            requestData.conversation_id = windowData.conversationId;
        }
        
        const params = new URLSearchParams(requestData);
        const eventSource = new EventSource('/api/prompt_stream?' + params.toString());

        eventSource.addEventListener('log', function(e) {
            const msg = JSON.parse(e.data);
            AIOntwikkelhulp.Formatting.addLogMessage(windowId, msg);
        });

        eventSource.addEventListener('final', function(e) {
            const data = JSON.parse(e.data);

            AIOntwikkelhulp.Formatting.removeLoadingMessage(windowId, loadingId);
            windowData.isWaitingForResponse = false;

            if (data.success) {
                if (Array.isArray(data.logs)) {
                    data.logs.forEach(log => AIOntwikkelhulp.Formatting.addLogMessage(windowId, log));
                }
                const content = data.content || data.message;
                AIOntwikkelhulp.Formatting.addMessageToChat(windowId, 'assistant', content);
                updateMcpStatus(data.active_mcp_servers);

                if (data.conversation_id && !windowData.conversationId) {
                    windowData.conversationId = data.conversation_id;
                    AIOntwikkelhulp.State.setLastConversationId(data.conversation_id);
                    const statusElement = windowElement.querySelector('.conversation-status');
                    statusElement.textContent = `Gesprek: ${data.title || 'Onbenoemd gesprek'}`;
                }

                // Hide activity indicator if this is a workflow tab
                if (windowData.workflowConfig && windowData.workflowConfig.tabId && AIOntwikkelhulp.Workflow) {
                    AIOntwikkelhulp.Workflow.hideActivityIndicator(windowData.workflowConfig.tabId);
                }

                // Check for queued prompts after response is complete
                if (windowData.queuedPrompt && AIOntwikkelhulp.Workflow) {
                    console.log('[Queue] Processing queued prompt for window', windowId);
                    const queuedPrompt = windowData.queuedPrompt;
                    const queuedConfig = windowData.queuedConfig;
                    windowData.queuedPrompt = null;
                    windowData.queuedConfig = null;
                    
                    // Process with delay to ensure UI is ready
                    setTimeout(() => {
                        console.log('[Queue] Executing queued workflow action');
                        AIOntwikkelhulp.Workflow.autoCreateTabWindow(queuedPrompt, queuedConfig);
                    }, 1000); // Increased delay
                }

                // Monitor response for workflow patterns
                if (AIOntwikkelhulp.Workflow) {
                    AIOntwikkelhulp.Workflow.monitorResponse(windowId, content);
                }

                // Handle chat away
                if (AIOntwikkelhulp.State.getChatAwayActive() && !AIOntwikkelhulp.State.getChatAwayInProgress() && AIOntwikkelhulp.ChatAway) {
                    AIOntwikkelhulp.ChatAway.forwardResponseToNextWindow(windowId, content);
                }
            } else {
                AIOntwikkelhulp.Formatting.addErrorMessage(windowId, data.error || 'Er is een fout opgetreden.');
                
                // Hide activity indicator on error
                if (windowData.workflowConfig && windowData.workflowConfig.tabId && AIOntwikkelhulp.Workflow) {
                    AIOntwikkelhulp.Workflow.hideActivityIndicator(windowData.workflowConfig.tabId);
                }
            }
            eventSource.close();
        });

        eventSource.addEventListener('error', function(err) {
            AIOntwikkelhulp.Formatting.removeLoadingMessage(windowId, loadingId);
            windowData.isWaitingForResponse = false;
            AIOntwikkelhulp.Formatting.addErrorMessage(windowId, 'Er is een fout opgetreden bij het verwerken van je vraag.');
            console.error('[Send Config] Error sending prompt:', err);
            
            // Hide activity indicator on error
            if (windowData.workflowConfig && windowData.workflowConfig.tabId && AIOntwikkelhulp.Workflow) {
                AIOntwikkelhulp.Workflow.hideActivityIndicator(windowData.workflowConfig.tabId);
            }
            
            eventSource.close();
        });
    }

    function sendPrompt(windowId, customInput = null) {
        const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
        if (!windowData || windowData.isWaitingForResponse) return;
        
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        const promptInput = windowElement.querySelector('.prompt-input');
        let prompt = customInput || promptInput.value.trim();

        if (prompt === '') {
            return;
        }
        
        // Check if this window has workflow configuration
        if (windowData.workflowConfig) {
            // Use the workflow configuration for model and preset
            const { model, preset } = windowData.workflowConfig;
            sendPromptWithConfig(windowId, prompt, model, preset);
            
            // Clear input only if it was not pre-filled
            if (!customInput) {
                promptInput.value = '';
            }
            return;
        }
        
        // Normal flow: use the selected values from the UI
        // Add user message to chat
        AIOntwikkelhulp.Formatting.addMessageToChat(windowId, 'user', prompt);
        
        // Clear input only if it was not pre-filled
        if (!customInput) {
            promptInput.value = '';
        }
        
        // Add loading indicator
        const loadingId = 'loading-' + Date.now();
        AIOntwikkelhulp.Formatting.addLoadingMessage(windowId, loadingId);
        
        // Get selected model and preset
        const modelSelect = windowElement.querySelector('.model-select');
        const presetSelect = windowElement.querySelector('.preset-select');
        
        // Validate that a proper model is selected (avoid placeholder option)
        const modelId = modelSelect.value;
        const selectedOption = modelSelect.options[modelSelect.selectedIndex];
        if (!modelId || (selectedOption && selectedOption.disabled)) {
            console.error('No valid model selected, cannot send prompt');
            AIOntwikkelhulp.Formatting.removeLoadingMessage(windowId, loadingId);
            AIOntwikkelhulp.Formatting.addErrorMessage(windowId, 'Geen geldig model geselecteerd. Wacht tot de modellen zijn geladen.');
            return;
        }
        
        const presetName = presetSelect.value;
        
        console.log(`Sending prompt with model: ${modelId}, preset: ${presetName || 'none'}`);
        
        // Set waiting flag
        windowData.isWaitingForResponse = true;
        
        // Prepare request
        const requestData = {
            prompt: prompt,
            model_id: modelId
        };
        
        // Add preset if selected
        if (presetName) {
            requestData.preset_name = presetName;
        }
        
        // Add conversation_id if continuing a conversation
        if (windowData.conversationId) {
            requestData.conversation_id = windowData.conversationId;
        }
        
        const params = new URLSearchParams(requestData);
        const eventSource = new EventSource('/api/prompt_stream?' + params.toString());

        eventSource.addEventListener('log', function(e) {
            const msg = JSON.parse(e.data);
            AIOntwikkelhulp.Formatting.addLogMessage(windowId, msg);
        });

        eventSource.addEventListener('final', function(e) {
            const data = JSON.parse(e.data);

            AIOntwikkelhulp.Formatting.removeLoadingMessage(windowId, loadingId);
            windowData.isWaitingForResponse = false;

            if (data.success) {
                if (Array.isArray(data.logs)) {
                    data.logs.forEach(log => AIOntwikkelhulp.Formatting.addLogMessage(windowId, log));
                }
                const content = data.content || data.message;
                AIOntwikkelhulp.Formatting.addMessageToChat(windowId, 'assistant', content);
                updateMcpStatus(data.active_mcp_servers);

                if (data.conversation_id && !windowData.conversationId) {
                    windowData.conversationId = data.conversation_id;
                    AIOntwikkelhulp.State.setLastConversationId(data.conversation_id);
                    const statusElement = windowElement.querySelector('.conversation-status');
                    statusElement.textContent = `Gesprek: ${data.title || 'Onbenoemd gesprek'}`;
                }

                // Monitor response for workflow patterns
                if (AIOntwikkelhulp.Workflow) {
                    AIOntwikkelhulp.Workflow.monitorResponse(windowId, content);
                }

                // Handle chat away
                if (AIOntwikkelhulp.State.getChatAwayActive() && !AIOntwikkelhulp.State.getChatAwayInProgress() && AIOntwikkelhulp.ChatAway) {
                    AIOntwikkelhulp.ChatAway.forwardResponseToNextWindow(windowId, content);
                }
            } else {
                AIOntwikkelhulp.Formatting.addErrorMessage(windowId, data.error || 'Er is een fout opgetreden.');
            }
            eventSource.close();
        });

        eventSource.addEventListener('error', function(err) {
            AIOntwikkelhulp.Formatting.removeLoadingMessage(windowId, loadingId);
            windowData.isWaitingForResponse = false;
            AIOntwikkelhulp.Formatting.addErrorMessage(windowId, 'Er is een fout opgetreden bij het verwerken van je vraag.');
            console.error('Error sending prompt:', err);
            eventSource.close();
        });
    }
    
    // Retry mechanisme voor het versturen van prompts
    async function sendPromptWithRetry(windowId, prompt, modelId, presetName, maxRetries = 3) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`[Send Prompt] Attempt ${attempt} of ${maxRetries}`);
                
                const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
                if (!windowElement) {
                    throw new Error(`Window element not found for ${windowId}`);
                }
                
                // Check if window is visible
                const isVisible = windowElement.offsetParent !== null;
                if (!isVisible) {
                    throw new Error(`Window ${windowId} is not visible`);
                }
                
                // Send the prompt
                await sendPromptWithConfig(windowId, prompt, modelId, presetName);
                console.log(`[Send Prompt] Success on attempt ${attempt}`);
                break;
                
            } catch (error) {
                console.error(`[Send Prompt] Attempt ${attempt} failed:`, error);
                
                if (attempt < maxRetries) {
                    console.log(`[Send Prompt] Retrying in 1 second...`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                } else {
                    console.error('[Send Prompt] All attempts failed');
                    throw error;
                }
            }
        }
    }
})();