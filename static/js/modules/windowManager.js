// Chat window management module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

AIOntwikkelhulp.WindowManager = (function() {
    
    // Public API
    return {
        createChatWindowElement: createChatWindowElement,
        initializeChatWindow: initializeChatWindow,
        setActiveWindow: setActiveWindow,
        addChatWindow: addChatWindow,
        removeActiveWindow: removeActiveWindow,
        changeLayout: changeLayout,
        getLayout: getLayout,
        updateChatAwayToggleVisibility: updateChatAwayToggleVisibility
    };
    
    function createChatWindowElement(windowId) {
        const newWindow = document.createElement('div');
        newWindow.className = 'chat-window';
        newWindow.setAttribute('data-window-id', windowId);

        newWindow.innerHTML = `
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-3">
                        <div>
                            <label for="model-select-${windowId}" class="form-label mb-0">Model:</label>
                            <select id="model-select-${windowId}" class="model-select form-select form-select-sm d-inline-block">
                                <option selected disabled>Modellen laden...</option>
                            </select>
                        </div>
                        <div>
                            <label for="preset-select-${windowId}" class="form-label mb-0">Preset:</label>
                            <select id="preset-select-${windowId}" 
                                    class="preset-select form-select form-select-sm d-inline-block"
                                    style="width: auto;"
                                    title="Selecteer een LLM preset voor specifieke use cases">
                                <option value="">Standaard</option>
                                <!-- Presets worden dynamisch geladen -->
                            </select>
                        </div>
                        <div id="workflow-status-${windowId}" class="workflow-status">
                            <span class="badge bg-info">
                                <i class="fas fa-cog"></i> Workflow
                            </span>
                        </div>
                    </div>
                    <div>
                        <button class="new-chat-btn btn btn-sm btn-outline-secondary">
                            <i class="fas fa-plus"></i> Nieuw gesprek
                        </button>
                    </div>
                </div>
                <div class="card-body d-flex flex-column">
                    <div class="chat-window-content flex-grow-1">
                        <div class="chat-column">
                            <div class="column-header">
                                <i class="fas fa-comments me-1"></i> Chat
                            </div>
                            <div class="chat-messages" id="chat-messages-${windowId}">
                                <!-- Chat messages will appear here -->
                            </div>
                        </div>
                        <div class="log-column">
                            <div class="column-header">
                                <i class="fas fa-list me-1"></i> Logs
                            </div>
                            <div class="log-messages" id="log-messages-${windowId}">
                                <!-- Log messages will appear here -->
                            </div>
                        </div>
                    </div>
                    <div class="chat-input mt-3">
                        <div class="input-group">
                            <textarea class="prompt-input form-control" id="input-${windowId}" placeholder="Stel je vraag aan Claude..." rows="3"></textarea>
                            <button class="send-prompt btn btn-primary" id="send-${windowId}">
                                <i class="fas fa-paper-plane"></i> Versturen
                            </button>
                        </div>
                        <div class="form-text text-end conversation-status">Nieuw gesprek</div>
                    </div>
                </div>
            </div>
        `;

        return newWindow;
    }
    
    function initializeChatWindow(windowElement) {
        const windowId = windowElement.getAttribute('data-window-id');
        
        // Store window data in the global state
        AIOntwikkelhulp.State.setChatWindow(windowId, {
            conversationId: null,
            isWaitingForResponse: false,
            workflowConfig: null,
            queuedPrompt: null,
            queuedConfig: null
        });
        
        // Add click event to make this window active
        windowElement.addEventListener('click', function(event) {
            // Don't make window active if clicking on a control element
            if (!event.target.closest('button, select, textarea')) {
                setActiveWindow(windowId);
            }
        });
        
        // Set up event listeners for this window
        const sendPromptBtn = windowElement.querySelector('.send-prompt');
        const promptInput = windowElement.querySelector('.prompt-input');
        const newChatBtn = windowElement.querySelector('.new-chat-btn');
        
        sendPromptBtn.addEventListener('click', function() {
            AIOntwikkelhulp.Network.sendPrompt(windowId);
        });
        
        promptInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                AIOntwikkelhulp.Network.sendPrompt(windowId);
            }
        });
        
        newChatBtn.addEventListener('click', function() {
            AIOntwikkelhulp.Network.resetConversation(windowId);
            
            // If workflow is active, configure the new chat with workflow settings
            if (AIOntwikkelhulp.State.getWorkflowActive() && AIOntwikkelhulp.Workflow) {
                setTimeout(() => {
                    AIOntwikkelhulp.Workflow.configureWorkflowWindow(windowElement);
                }, 100);
            }
        });
        
        // Load available models for this window
        const modelSelectEl = windowElement.querySelector('.model-select');
        AIOntwikkelhulp.Network.populateModelSelect(modelSelectEl);

        // Load available presets for this window
        const presetSelectEl = windowElement.querySelector('.preset-select');
        AIOntwikkelhulp.Network.populatePresetSelect(presetSelectEl);

        // Make this window active
        setActiveWindow(windowId);
        
        // Update chat away toggle visibility
        updateChatAwayToggleVisibility();
    }

    function setActiveWindow(windowId) {
        // Remove active class from all windows
        document.querySelectorAll('.chat-window').forEach(window => {
            window.classList.remove('active');
        });
        
        // Add active class to the clicked window
        const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
        if (windowElement) {
            windowElement.classList.add('active');
            
            // Enable the remove window button if there's more than one window
            const removeBtn = document.getElementById('remove-window-btn');
            removeBtn.disabled = document.querySelectorAll('.chat-window').length <= 1;
        }
    }

    function addChatWindow(initialInput, isWorkflowWindow = false, workflowConfig = null) {
        return new Promise((resolve) => {
            const windowsContainer = document.getElementById('chat-windows-container');
            const currentWindows = document.querySelectorAll('.chat-window');
            const newWindowId = `window-${currentWindows.length + 1}`;

            const newWindow = document.createElement('div');
            newWindow.className = 'chat-window';
            newWindow.setAttribute('data-window-id', newWindowId);

            newWindow.innerHTML = `
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center gap-3">
                            <div>
                                <label for="model-select-${newWindowId}" class="form-label mb-0">Model:</label>
                                <select id="model-select-${newWindowId}" class="model-select form-select form-select-sm d-inline-block">
                                    <option selected disabled>Modellen laden...</option>
                                </select>
                            </div>
                            <div>
                                <label for="preset-select-${newWindowId}" class="form-label mb-0">Preset:</label>
                                <select id="preset-select-${newWindowId}" 
                                        class="preset-select form-select form-select-sm d-inline-block"
                                        style="width: auto;"
                                        title="Selecteer een LLM preset voor specifieke use cases">
                                    <option value="">Standaard</option>
                                    <!-- Presets worden dynamisch geladen -->
                                </select>
                            </div>
                            <div id="workflow-status-${newWindowId}" class="workflow-status d-none">
                                <span class="badge bg-info">
                                    <i class="fas fa-cog"></i> Workflow
                                </span>
                            </div>
                        </div>
                        <div>
                            <button class="new-chat-btn btn btn-sm btn-outline-secondary">
                                <i class="fas fa-plus"></i> Nieuw gesprek
                            </button>
                        </div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <div class="chat-window-content flex-grow-1">
                            <div class="chat-column">
                                <div class="column-header">
                                    <i class="fas fa-comments me-1"></i> Chat
                                </div>
                                <div class="chat-messages" id="chat-messages-${newWindowId}">
                                    <!-- Chat messages will appear here -->
                                </div>
                            </div>
                            <div class="log-column">
                                <div class="column-header">
                                    <i class="fas fa-list me-1"></i> Logs
                                </div>
                                <div class="log-messages" id="log-messages-${newWindowId}">
                                    <!-- Log messages will appear here -->
                                </div>
                            </div>
                        </div>
                        <div class="chat-input mt-3">
                            <div class="input-group">
                                <textarea class="prompt-input form-control" id="input-${newWindowId}" placeholder="Stel je vraag aan Claude..." rows="3">${''}</textarea>
                                <button class="send-prompt btn btn-primary" id="send-${newWindowId}">
                                    <i class="fas fa-paper-plane"></i> Versturen
                                </button>
                            </div>
                            <div class="form-text text-end conversation-status">Nieuw gesprek</div>
                        </div>
                    </div>
                </div>
            `;

            // Add the new window to the container
            windowsContainer.appendChild(newWindow);

            setTimeout(() => {
                console.log(`Initializing new chat window: ${newWindowId}`); // Debugging
                initializeChatWindow(newWindow);
                const modelSelectEl = newWindow.querySelector('.model-select');
                const presetSelectEl = newWindow.querySelector('.preset-select');
                AIOntwikkelhulp.Network.populateModelSelect(modelSelectEl);
                AIOntwikkelhulp.Network.populatePresetSelect(presetSelectEl);

                const finalize = () => {
                    setActiveWindow(newWindowId);
                    resolve(newWindow);
                };

                if (isWorkflowWindow && AIOntwikkelhulp.Workflow) {
                    setTimeout(() => {
                        AIOntwikkelhulp.Workflow.configureWorkflowWindow(newWindow, workflowConfig).then(finalize);
                    }, 500); // Wait for selects to be populated
                } else {
                    finalize();
                }
            }, 100);

            // Automatically send the initial input if there is one
            if (initialInput) {
                console.log("Adding last Claude response as user input:", initialInput); // Debugging
                
                setTimeout(() => {
                    AIOntwikkelhulp.Network.sendPrompt(newWindowId, initialInput + ' Kun je me hier wat meer over vertellen?');
                }, 500); // Small delay to simulate user interaction
            }

            // Setup event listener for the send button
            document.getElementById(`send-${newWindowId}`).addEventListener('click', function() {
                AIOntwikkelhulp.Network.sendPrompt(newWindowId);
            });
        });
    }
    
    function removeActiveWindow() {
        const activeWindow = document.querySelector('.chat-window.active');
        if (!activeWindow) return;
        
        const windowId = activeWindow.getAttribute('data-window-id');
        
        // Remove from global state
        AIOntwikkelhulp.State.deleteChatWindow(windowId);
        
        // Remove the element
        activeWindow.remove();
        
        // Set another window as active if available
        const remainingWindows = document.querySelectorAll('.chat-window');
        if (remainingWindows.length > 0) {
            const firstWindow = remainingWindows[0];
            setActiveWindow(firstWindow.getAttribute('data-window-id'));
        }
        
        // Disable remove button if only one window remains
        if (remainingWindows.length <= 1) {
            document.getElementById('remove-window-btn').disabled = true;
        }
        
        // Update chat away toggle visibility
        updateChatAwayToggleVisibility();
        
        // If chat away is active but we don't have at least 2 windows, turn it off
        if (AIOntwikkelhulp.State.getChatAwayActive() && remainingWindows.length < 2) {
            const chatAwayToggle = document.getElementById('chat-away-toggle');
            chatAwayToggle.checked = false;
            AIOntwikkelhulp.State.setChatAwayActive(false);
        }
    }

    function getLayout() {
        const container = document.getElementById('chat-windows-container');
        if (container.classList.contains('layout-horizontal')) return 'horizontal';
        if (container.classList.contains('layout-grid')) return 'grid';
        return 'single';
    }

    function changeLayout(layout) {
        const container = document.getElementById('chat-windows-container');
        const layoutButtons = document.querySelectorAll('.window-layout-controls .btn');
        
        // Remove all layout classes
        container.classList.remove('layout-single', 'layout-horizontal', 'layout-grid');
        
        // Remove active class from all layout buttons
        layoutButtons.forEach(btn => btn.classList.remove('active'));
        
        // Add appropriate class and activate the correct button
        switch (layout) {
            case 'horizontal':
                container.classList.add('layout-horizontal');
                document.getElementById('layout-horizontal').classList.add('active');
                break;
            case 'grid':
                container.classList.add('layout-grid');
                document.getElementById('layout-grid').classList.add('active');
                break;
            default: // single
                container.classList.add('layout-single');
                document.getElementById('layout-single').classList.add('active');
                break;
        }
    }
    
    // Function to show/hide the chat away button based on the number of windows
    function updateChatAwayToggleVisibility() {
        const chatAwayContainer = document.getElementById('chat-away-container');
        const chatWindows = document.querySelectorAll('.chat-window');
        
        if (chatWindows.length >= 2) {
            chatAwayContainer.classList.remove('d-none');
        } else {
            chatAwayContainer.classList.add('d-none');
            // Make sure chat away is turned off if we don't have at least 2 windows
            const chatAwayToggle = document.getElementById('chat-away-toggle');
            if (chatAwayToggle.checked) {
                chatAwayToggle.checked = false;
                AIOntwikkelhulp.State.setChatAwayActive(false);
            }
        }
    }
})();