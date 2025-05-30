// Global state for all windows
const chatWindows = new Map();

// Chat away state
let chatAwayActive = false;
let chatAwayInProgress = false;
let lastConversationId = null;

// Workflow state
let workflowActive = false;
let workflowTabsInitialized = false;

// Global presets cache
let availablePresets = {};

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

// Workflow patterns
const workflowPatterns = {
    issueCreation: /Ik heb issue #?(\d+) aangemaakt voor Repo ([^\/]+)\/([^\s]+)/i,
    prCreation: /Ik heb Pull Request #?(\d+) aangemaakt voor Repo ([^\/]+)\/([^\s]+)/i,
    prProcessed: /Ik heb Pull Request #?(\d+) verwerkt en bijbehorende branche(?:([^\s]+))? verwijderd voor Repo ([^\/]+)\/([^\s.]+)\.?/i
};

// Workflow configuration with model and preset settings per pattern
const workflowConfig = {
    issueCreation: {
        pattern: workflowPatterns.issueCreation,
        action: "Ga naar Repo [owner]/[repo] en pak issue [nummer] op",
        model: "claude-sonnet-4-20250514",
        preset: "developer_agent",
        description: "Issue Creation - Developer Agent met Claude Sonnet 4",
        tabId: "issue-tab"
    },
    prCreation: {
        pattern: workflowPatterns.prCreation,
        action: "Ga naar Repo [owner]/[repo] en merge Pull Request [nummer] en delete de bijbehorende branche",
        model: "claude-3-5-haiku-20241022",
        preset: "developer_agent",
        description: "PR Creation - Developer Agent met Claude Haiku 3.5",
        tabId: "pr-tab"
    },
    prProcessed: {
        pattern: workflowPatterns.prProcessed,
        action: "Ga Repo [owner]/[repo]",
        model: "claude-opus-4-20250514",
        preset: "creative_writing",        
        description: "PR Processed - Developer Agent met Claude Opus 4",
        tabId: "processed-tab"
    }
};

// Fallback configuration
const FALLBACK_MODEL_ID = 'claude-sonnet-4-20250514';
const FALLBACK_PRESET_ID = 'developer_agent';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the first window
    const firstWindow = document.querySelector('.chat-window');
    if (firstWindow) {
        initializeChatWindow(firstWindow);
    }
    
    // Setup control panel buttons
    setupControlPanel();
    
    // Check URL parameters to load conversations
    checkUrlParams();
    
    // Load workflow state from localStorage
    loadWorkflowState();

    // Voeg event listener toe voor de nieuwe knop
    const continueInNewWindowBtn = document.getElementById('continue-in-new-window-btn');
    continueInNewWindowBtn.addEventListener('click', function() {
        // Haal het laatste bericht van Claude op
        fetchLastAssistantMessage()
            .then(lastMessage => {
                // Open een nieuw venster met het laatste bericht
                addChatWindow(lastMessage);

                // Sluit het actieve venster
                removeActiveWindow();
            })
            .catch(() => {
                // Als er geen bericht is, open een nieuw venster zonder prompt
                addChatWindow('');
                removeActiveWindow();
            });
    });
});

function loadWorkflowState() {
    const savedState = localStorage.getItem('workflowActive');
    if (savedState !== null) {
        workflowActive = savedState === 'true';
        const workflowToggle = document.getElementById('workflow-toggle');
        if (workflowToggle) {
            workflowToggle.checked = workflowActive;
        }
        
        // Initialize workflow tabs if workflow is active
        if (workflowActive) {
            toggleWorkflowMode(true);
        }
    }
}

function saveWorkflowState() {
    localStorage.setItem('workflowActive', workflowActive.toString());
}

function toggleWorkflow() {
    const workflowToggle = document.getElementById('workflow-toggle');
    workflowActive = workflowToggle.checked;
    saveWorkflowState();
    
    toggleWorkflowMode(workflowActive);
}

function toggleWorkflowMode(activate) {
    const workflowTabsContainer = document.getElementById('workflow-tabs-container');
    const chatWindowsContainer = document.getElementById('chat-windows-container');
    
    if (activate) {
        console.log('Workflow mode activated - switching to tabs');
        
        // Hide regular chat windows container
        chatWindowsContainer.classList.add('d-none');
        
        // Show workflow tabs container
        workflowTabsContainer.classList.remove('d-none');
        
        // Initialize workflow tabs if not already done
        if (!workflowTabsInitialized) {
            initializeWorkflowTabs();
            workflowTabsInitialized = true;
        }
    } else {
        console.log('Workflow mode deactivated - switching to regular windows');
        
        // Show regular chat windows container
        chatWindowsContainer.classList.remove('d-none');
        
        // Hide workflow tabs container
        workflowTabsContainer.classList.add('d-none');
    }
}

function initializeWorkflowTabs() {
    console.log('Initializing workflow tabs');
    
    const tabs = {
        'issue-tab': workflowConfig.issueCreation,
        'pr-tab': workflowConfig.prCreation,
        'processed-tab': workflowConfig.prProcessed
    };
    
    for (const [tabId, config] of Object.entries(tabs)) {
        const tabPane = document.getElementById(tabId);
        const windowId = `workflow-${tabId}`;
        
        // Check if window already exists
        if (document.querySelector(`[data-window-id="${windowId}"]`)) {
            console.log(`Window ${windowId} already exists, skipping creation`);
            continue;
        }
        
        // Create chat window in the tab
        const chatWindow = createChatWindowElement(windowId);
        tabPane.appendChild(chatWindow);
        
        // Initialize with workflow configuration
        initializeChatWindow(chatWindow);
        
        // Mark window as workflow window immediately
        const windowData = chatWindows.get(windowId);
        if (windowData) {
            windowData.isWorkflowWindow = true;
            windowData.workflowTabId = tabId;
        }
        
        // Configure the window with workflow settings
        setTimeout(() => {
            configureWorkflowWindow(chatWindow, config);
        }, 500);
    }
}

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

function monitorResponse(windowId, content) {
    // Only monitor if workflow is active
    if (!workflowActive) {
        console.log('[Workflow Monitor] Workflow not active, skipping pattern monitoring');
        return;
    }
    
    console.log(`[Workflow Monitor] Checking response from window ${windowId}`);
    console.log('[Workflow Monitor] Content:', content.substring(0, 100) + '...');
    
    // Check each workflow pattern and use the appropriate configuration
    for (const [patternName, config] of Object.entries(workflowConfig)) {
        const match = content.match(config.pattern);
        if (match) {
            console.log(`[Workflow Monitor] ✓ Pattern "${patternName}" matched`);
            console.log('[Workflow Monitor] Match details:', match);
            console.log('[Workflow Monitor] Pattern config:', config);
            
            let prompt;
            if (patternName === 'issueCreation') {
                const [, issueNumber, owner, repo] = match;
                prompt = `Ga naar Repo ${owner}/${repo} en pak issue ${issueNumber} op`;
            } else if (patternName === 'prCreation') {
                const [, prNumber, owner, repo] = match;
                prompt = `Ga naar Repo ${owner}/${repo} en merge Pull Request ${prNumber} en delete de bijbehorende branche`;
            } else if (patternName === 'prProcessed') {
                const [, prNumber, branch, owner, repo] = match;
                prompt = `Ga Repo ${owner}/${repo}`;
            }
            
            console.log(`[Workflow Monitor] Calling autoCreateChatWindow with prompt: "${prompt}"`);
            autoCreateChatWindow(prompt, windowId, config);
            return;
        }
    }
    
    console.log('[Workflow Monitor] No workflow patterns detected in response');
}

async function autoCreateChatWindow(prompt, currentWindowId, workflowConfig) {
    console.log('[Workflow] Auto-creating new chat window with prompt:', prompt);
    console.log('[Workflow] Using workflow config:', workflowConfig);

    // Add a small delay to ensure the current response is fully processed
    setTimeout(async () => {
        try {
            if (workflowActive && workflowConfig.tabId) {
                // Use tab-based workflow
                autoCreateTabWindow(prompt, workflowConfig);
            } else {
                // Use regular window workflow
                const newWindow = await addChatWindow('', true, workflowConfig);
                const newWindowId = newWindow.getAttribute('data-window-id');

                // Wait for configuration to complete before sending prompt
                setTimeout(() => {
                    sendPromptWithConfig(newWindowId, prompt, workflowConfig.model, workflowConfig.preset);
                }, 1000);

                // Close the current window after a short delay
                setTimeout(() => {
                    autoCloseWindow(currentWindowId);
                }, 1500);
            }
        } catch (error) {
            console.error('[Workflow] Error configuring workflow window:', error);
        }
    }, 1000);
}

function autoCreateTabWindow(prompt, workflowConfig) {
    console.log('[Tab Workflow] Auto-creating tab window for:', workflowConfig.description);
    
    const targetTabId = workflowConfig.tabId;
    const windowId = `workflow-${targetTabId}`;
    
    // Check if window exists and is ready
    const windowData = chatWindows.get(windowId);
    if (!windowData) {
        console.error(`[Tab Workflow] Window ${windowId} not found in chatWindows`);
        return;
    }
    
    // Check if window is not waiting for response
    if (windowData.isWaitingForResponse) {
        console.log(`[Tab Workflow] Window ${windowId} is still waiting for response, queueing prompt`);
        windowData.queuedPrompt = prompt;
        windowData.queuedConfig = workflowConfig;
        return;
    }
    
    // Get the tab button
    const tabButton = document.querySelector(`[data-bs-target="#${targetTabId}"]`);
    if (!tabButton) {
        console.error(`[Tab Workflow] Tab button for ${targetTabId} not found`);
        return;
    }
    
    // Check if tab is already active
    const isTabActive = tabButton.classList.contains('active');
    
    if (isTabActive) {
        // Tab is already active, send prompt immediately
        console.log('[Tab Workflow] Tab already active, sending prompt directly');
        showActivityIndicator(targetTabId);
        sendPromptWithRetry(windowId, prompt, workflowConfig.model, workflowConfig.preset);
    } else {
        // Need to switch tabs first
        console.log('[Tab Workflow] Switching to tab before sending prompt');
        
        // Create promise to handle tab switch completion
        const tabSwitchPromise = new Promise((resolve) => {
            const onTabShown = function() {
                tabButton.removeEventListener('shown.bs.tab', onTabShown);
                console.log('[Tab Workflow] Tab switch event fired');
                resolve();
            };
            tabButton.addEventListener('shown.bs.tab', onTabShown);
            
            // Activate the tab
            const tab = new bootstrap.Tab(tabButton);
            tab.show();
            
            // Timeout fallback in case event doesn't fire
            setTimeout(() => {
                console.log('[Tab Workflow] Tab switch timeout fallback triggered');
                resolve();
            }, 500);
        });
        
        // Wait for tab switch and then send prompt
        tabSwitchPromise.then(() => {
            console.log('[Tab Workflow] Tab switch complete, sending prompt');
            showActivityIndicator(targetTabId);
            
            // Additional delay to ensure DOM is ready
            setTimeout(() => {
                sendPromptWithRetry(windowId, prompt, workflowConfig.model, workflowConfig.preset);
            }, 200);
        });
    }
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

// Activity indicator functies
function showActivityIndicator(tabId) {
    const indicator = document.querySelector(`[data-bs-target="#${tabId}"] .activity-indicator`);
    if (indicator) {
        indicator.style.display = 'inline';
        console.log(`[Activity] Showing indicator for tab ${tabId}`);
    }
}

function hideActivityIndicator(tabId) {
    const indicator = document.querySelector(`[data-bs-target="#${tabId}"] .activity-indicator`);
    if (indicator) {
        indicator.style.display = 'none';
        console.log(`[Activity] Hiding indicator for tab ${tabId}`);
    }
}

function configureWorkflowWindow(windowElement, config = null) {
    console.log('[Workflow Config] Configuring window for workflow mode');
    
    return new Promise((resolve, reject) => {
        if (config) {
            console.log('[Workflow Config] Workflow configuration:', {
                model: config.model,
                preset: config.preset,
                description: config.description
            });
        }
        
        // Use provided config or default workflow config
        const modelId = config ? config.model : FALLBACK_MODEL_ID;
        const presetId = config ? config.preset : FALLBACK_PRESET_ID;
        const description = config ? config.description : 'Workflow mode';

        // Store the workflow configuration in the window data
        const windowId = windowElement.getAttribute('data-window-id');
        const windowData = chatWindows.get(windowId);
        if (windowData) {
            windowData.workflowConfig = {
                model: modelId,
                preset: presetId,
                description: description,
                tabId: config ? config.tabId : null
            };
        }

        addLogMessage(
            windowId,
            `Workflow configuratie ontvangen: model ${modelId}, preset ${presetId || 'geen'}`
        );
        
        console.log(`[Workflow Config] Applying workflow config: ${description}`);
        console.log(`[Workflow Config] Target model: ${modelId}, Target preset: ${presetId}`);
        
        // Show workflow status badge
        const workflowStatus = windowElement.querySelector('.workflow-status');
        if (workflowStatus) {
            workflowStatus.classList.remove('d-none');
            const badge = workflowStatus.querySelector('.badge');
            if (badge) {
                badge.title = description;
            }
        }
        
        // Wait for models and presets to be loaded before configuring
        const modelSelect = windowElement.querySelector('.model-select');
        const presetSelect = windowElement.querySelector('.preset-select');
        
        let modelsLoaded = false;
        let presetsLoaded = false;
        
        const checkCompletion = () => {
            if (modelsLoaded && presetsLoaded) {
                console.log('[Workflow Config] ✓ Both models and presets loaded, configuration complete');
                addLogMessage(
                    windowId,
                    `Model gebruikt: ${modelSelect.value}, preset: ${presetSelect.value || 'geen'}`
                );
                resolve();
            }
        };
        
        // Set model with promise-based approach
        const configureModel = () => {
            return new Promise((resolveModel) => {
                const setModel = () => {
                    if (!modelSelect || modelSelect.options.length <= 1) {
                        // Models not loaded yet, wait a bit more
                        setTimeout(setModel, 100);
                        return;
                    }
                    
                    let modelSet = false;
                    for (let i = 0; i < modelSelect.options.length; i++) {
                        if (modelSelect.options[i].value === modelId) {
                            modelSelect.selectedIndex = i;
                            console.log(`[Workflow Config] ✓ Model set to: ${modelId}`);
                            modelSet = true;
                            break;
                        }
                    }
                    
                    if (!modelSet) {
                        // Try fallback model
                        for (let i = 0; i < modelSelect.options.length; i++) {
                            if (modelSelect.options[i].value === FALLBACK_MODEL_ID) {
                                modelSelect.selectedIndex = i;
                                console.warn(`[Workflow Config] ⚠ Model ${modelId} not found, using fallback: ${FALLBACK_MODEL_ID}`);
                                addLogMessage(windowId, 
                                    `Waarschuwing: Model ${modelId} niet beschikbaar, teruggevallen op ${FALLBACK_MODEL_ID}`);
                                break;
                            }
                        }
                    }
                    
                    modelsLoaded = true;
                    resolveModel();
                    checkCompletion();
                };
                
                setModel();
            });
        };
        
        // Set preset with promise-based approach
        const configurePreset = () => {
            return new Promise((resolvePreset) => {
                const setPreset = () => {
                    if (!presetSelect || presetSelect.options.length <= 1) {
                        // Presets not loaded yet, wait a bit more
                        setTimeout(setPreset, 100);
                        return;
                    }
                    
                    let presetSet = false;
                    for (let i = 0; i < presetSelect.options.length; i++) {
                        if (presetSelect.options[i].value === presetId) {
                            presetSelect.selectedIndex = i;
                            console.log(`[Workflow Config] ✓ Preset set to: ${presetId}`);
                            presetSet = true;
                            break;
                        }
                    }
                    
                    if (!presetSet && presetId) {
                        // Try fallback preset
                        for (let i = 0; i < presetSelect.options.length; i++) {
                            if (presetSelect.options[i].value === FALLBACK_PRESET_ID) {
                                presetSelect.selectedIndex = i;
                                console.warn(`[Workflow Config] ⚠ Preset ${presetId} not found, using fallback: ${FALLBACK_PRESET_ID}`);
                                addLogMessage(windowId, 
                                    `Waarschuwing: Preset ${presetId} niet beschikbaar, teruggevallen op ${FALLBACK_PRESET_ID}`);
                                break;
                            }
                        }
                        
                        if (!presetSet) {
                            // Use no preset (default)
                            presetSelect.selectedIndex = 0;
                            console.warn(`[Workflow Config] ⚠ Preset ${presetId} and fallback not found, using default`);
                            addLogMessage(windowId, 
                                `Waarschuwing: Preset ${presetId} niet beschikbaar, geen preset gebruikt`);
                        }
                    }
                    
                    presetsLoaded = true;
                    resolvePreset();
                    checkCompletion();
                };
                
                setPreset();
            });
        };
        
        // Configure both model and preset
        configureModel();
        configurePreset();
        
        // Set a timeout to prevent hanging
        setTimeout(() => {
            if (!modelsLoaded || !presetsLoaded) {
                console.warn('[Workflow Config] ⚠ Configuration timeout, proceeding with current settings');
                reject(new Error('Configuration timeout'));
            }
        }, 5000);
    });
}

function autoCloseWindow(windowId) {
    console.log('Auto-closing window:', windowId);
    
    const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
    if (!windowElement) return;
    
    // Make sure we're not closing the last window
    const allWindows = document.querySelectorAll('.chat-window');
    if (allWindows.length <= 1) {
        console.log('Cannot close the last window');
        return;
    }
    
    // Remove from global state
    chatWindows.delete(windowId);
    
    // Remove the element
    windowElement.remove();
    
    // Set another window as active if needed
    const remainingWindows = document.querySelectorAll('.chat-window');
    if (remainingWindows.length > 0) {
        const lastWindow = remainingWindows[remainingWindows.length - 1];
        setActiveWindow(lastWindow.getAttribute('data-window-id'));
    }
    
    // Update UI elements
    updateChatAwayToggleVisibility();
    
    // Disable remove button if only one window remains
    if (remainingWindows.length <= 1) {
        document.getElementById('remove-window-btn').disabled = true;
    }
}

function fetchLastAssistantMessage() {
    return new Promise((resolve, reject) => {
        const lastConversationId = getLastConversationId();

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
                availablePresets = data.presets;
                
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

function setupControlPanel() {
    // Add window button
    const addWindowBtn = document.getElementById('add-window-btn');
    addWindowBtn.removeEventListener('click', addChatWindow); // Ensures it's not duplicated
    addWindowBtn.addEventListener('click', function() {
        const conversationId = getLastConversationId(); // Get the current conversation ID
        if (conversationId) {
            fetchLastAssistantMessage(conversationId)
                .then(lastMessage => {
                    // Check if workflow is active and configure accordingly
                    const isWorkflowWindow = workflowActive;
                    addChatWindow(lastMessage, isWorkflowWindow);
                })
                .catch(() => {
                    const isWorkflowWindow = workflowActive;
                    addChatWindow('', isWorkflowWindow);
                });
        } else {
            const isWorkflowWindow = workflowActive;
            addChatWindow('', isWorkflowWindow);
        }
    });
    
    // Remove window button
    document.getElementById('remove-window-btn').addEventListener('click', removeActiveWindow);
    
    // Layout buttons
    document.getElementById('layout-single').addEventListener('click', () => changeLayout('single'));
    document.getElementById('layout-horizontal').addEventListener('click', () => changeLayout('horizontal'));
    document.getElementById('layout-grid').addEventListener('click', () => changeLayout('grid'));
    
    // Chat away toggle
    document.getElementById('chat-away-toggle').addEventListener('change', function(e) {
        chatAwayActive = e.target.checked;
        if (chatAwayActive) {
            // Start the chat away process when activated
            startChatAway();
        } else {
            // Stop the chat away process when deactivated
            stopChatAway();
        }
    });
    
    // Workflow toggle
    document.getElementById('workflow-toggle').addEventListener('change', toggleWorkflow);
}

function setLastConversationId(conversationId) {
    if (conversationId) {
        lastConversationId= conversationId;
    }
}

function getLastConversationId() {
    return lastConversationId;
}

function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const conversationId = urlParams.get('conversation_id');
    
    if (conversationId) {
        const firstWindow = document.querySelector('.chat-window');
        if (firstWindow) {
            const windowId = firstWindow.getAttribute('data-window-id');
            const windowData = chatWindows.get(windowId);
            if (windowData) {
                loadConversation(windowId, conversationId);
            }
        }
    }
}

function initializeChatWindow(windowElement) {
    const windowId = windowElement.getAttribute('data-window-id');
    
    // Store window data in the global state
    chatWindows.set(windowId, {
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
        sendPrompt(windowId);
    });
    
    promptInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendPrompt(windowId);
        }
    });
    
    newChatBtn.addEventListener('click', function() {
        resetConversation(windowId);
        
        // If workflow is active, configure the new chat with workflow settings
        if (workflowActive) {
            setTimeout(() => {
                configureWorkflowWindow(windowElement);
            }, 100);
        }
    });
    
    // Load available models for this window
    const modelSelectEl = windowElement.querySelector('.model-select');
    populateModelSelect(modelSelectEl);

    // Load available presets for this window
    const presetSelectEl = windowElement.querySelector('.preset-select');
    populatePresetSelect(presetSelectEl);

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
        populateModelSelect(modelSelectEl);
        populatePresetSelect(presetSelectEl);

        const finalize = () => {
            setActiveWindow(newWindowId);
            resolve(newWindow);
        };

        if (isWorkflowWindow) {
            setTimeout(() => {
                configureWorkflowWindow(newWindow, workflowConfig).then(finalize);
            }, 500); // Wait for selects to be populated
        } else {
            finalize();
        }
    }, 100);

    // Automatically send the initial input if there is one
    if (initialInput) {
        console.log("Adding last Claude response as user input:", initialInput); // Debugging
        
        //addMessageToChat(newWindowId, 'user', initialInput);

        setTimeout(() => {
            sendPrompt(newWindowId, initialInput + ' Kun je me hier wat meer over vertellen?');
        }, 500); // Small delay to simulate user interaction
    }

    // Setup event listener for the send button
    document.getElementById(`send-${newWindowId}`).addEventListener('click', function() {
        sendPrompt(newWindowId);
    });
    });
}
function removeActiveWindow() {
    const activeWindow = document.querySelector('.chat-window.active');
    if (!activeWindow) return;
    
    const windowId = activeWindow.getAttribute('data-window-id');
    
    // Remove from global state
    chatWindows.delete(windowId);
    
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
    if (chatAwayActive && remainingWindows.length < 2) {
        const chatAwayToggle = document.getElementById('chat-away-toggle');
        chatAwayToggle.checked = false;
        chatAwayActive = false;
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

function loadConversation(windowId, conversationId) {
    const windowData = chatWindows.get(windowId);
    if (!windowData) return;
    
    windowData.conversationId = conversationId;
    //setLastConversationId(conversationId); 

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
                        addLogMessage(windowId, message.content);
                    } else {
                        addMessageToChat(windowId, message.role, message.content);
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
    const windowData = chatWindows.get(windowId);
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
    const windowData = chatWindows.get(windowId);
    if (!windowData || windowData.isWaitingForResponse) return;
    
    const windowElement = document.querySelector(`[data-window-id="${windowId}"]`);
    
    if (!prompt || prompt.trim() === '') {
        return;
    }
    
    // Add user message to chat
    addMessageToChat(windowId, 'user', prompt);
    
    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    addLoadingMessage(windowId, loadingId);
    
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
        addLogMessage(windowId, msg);
    });

    eventSource.addEventListener('final', function(e) {
        const data = JSON.parse(e.data);

        removeLoadingMessage(windowId, loadingId);
        windowData.isWaitingForResponse = false;

        if (data.success) {
            if (Array.isArray(data.logs)) {
                data.logs.forEach(log => addLogMessage(windowId, log));
            }
            const content = data.content || data.message;
            addMessageToChat(windowId, 'assistant', content);
            updateMcpStatus(data.active_mcp_servers);

            if (data.conversation_id && !windowData.conversationId) {
                windowData.conversationId = data.conversation_id;
                setLastConversationId(data.conversation_id);
                const statusElement = windowElement.querySelector('.conversation-status');
                statusElement.textContent = `Gesprek: ${data.title || 'Onbenoemd gesprek'}`;
            }

            // Hide activity indicator if this is a workflow tab
            if (windowData.workflowConfig && windowData.workflowConfig.tabId) {
                hideActivityIndicator(windowData.workflowConfig.tabId);
            }

            // Check for queued prompts after response is complete
            if (windowData.queuedPrompt) {
                console.log('[Queue] Processing queued prompt for window', windowId);
                const queuedPrompt = windowData.queuedPrompt;
                const queuedConfig = windowData.queuedConfig;
                windowData.queuedPrompt = null;
                windowData.queuedConfig = null;
                
                // Process with delay to ensure UI is ready
                setTimeout(() => {
                    console.log('[Queue] Executing queued workflow action');
                    autoCreateTabWindow(queuedPrompt, queuedConfig);
                }, 1000); // Increased delay
            }

            // Monitor response for workflow patterns
            monitorResponse(windowId, content);

            if (chatAwayActive && !chatAwayInProgress) {
                forwardResponseToNextWindow(windowId, content);
            }
        } else {
            addErrorMessage(windowId, data.error || 'Er is een fout opgetreden.');
            
            // Hide activity indicator on error
            if (windowData.workflowConfig && windowData.workflowConfig.tabId) {
                hideActivityIndicator(windowData.workflowConfig.tabId);
            }
        }
        eventSource.close();
    });

    eventSource.addEventListener('error', function(err) {
        removeLoadingMessage(windowId, loadingId);
        windowData.isWaitingForResponse = false;
        addErrorMessage(windowId, 'Er is een fout opgetreden bij het verwerken van je vraag.');
        console.error('[Send Config] Error sending prompt:', err);
        
        // Hide activity indicator on error
        if (windowData.workflowConfig && windowData.workflowConfig.tabId) {
            hideActivityIndicator(windowData.workflowConfig.tabId);
        }
        
        eventSource.close();
    });
}

function sendPrompt(windowId, customInput = null) {
    const windowData = chatWindows.get(windowId);
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
    addMessageToChat(windowId, 'user', prompt);
    
    // Clear input only if it was not pre-filled
    if (!customInput) {
        promptInput.value = '';
    }
    
    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    addLoadingMessage(windowId, loadingId);
    
    // Get selected model and preset
    const modelSelect = windowElement.querySelector('.model-select');
    const presetSelect = windowElement.querySelector('.preset-select');
    
    // Validate that a proper model is selected (avoid placeholder option)
    const modelId = modelSelect.value;
    // if (!modelId || modelId === '' || modelSelect.selectedIndex === 0) {
    const selectedOption = modelSelect.options[modelSelect.selectedIndex];
    if (!modelId || (selectedOption && selectedOption.disabled)) {
        console.error('No valid model selected, cannot send prompt');
        removeLoadingMessage(windowId, loadingId);
        addErrorMessage(windowId, 'Geen geldig model geselecteerd. Wacht tot de modellen zijn geladen.');
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
        addLogMessage(windowId, msg);
    });

    eventSource.addEventListener('final', function(e) {
        const data = JSON.parse(e.data);

        removeLoadingMessage(windowId, loadingId);
        windowData.isWaitingForResponse = false;

        if (data.success) {
            if (Array.isArray(data.logs)) {
                data.logs.forEach(log => addLogMessage(windowId, log));
            }
            const content = data.content || data.message;
            addMessageToChat(windowId, 'assistant', content);
            updateMcpStatus(data.active_mcp_servers);

            if (data.conversation_id && !windowData.conversationId) {
                windowData.conversationId = data.conversation_id;
                setLastConversationId(data.conversation_id);
                const statusElement = windowElement.querySelector('.conversation-status');
                statusElement.textContent = `Gesprek: ${data.title || 'Onbenoemd gesprek'}`;
            }

            // Monitor response for workflow patterns
            monitorResponse(windowId, content);

            if (chatAwayActive && !chatAwayInProgress) {
                forwardResponseToNextWindow(windowId, content);
            }
        } else {
            addErrorMessage(windowId, data.error || 'Er is een fout opgetreden.');
        }
        eventSource.close();
    });

    eventSource.addEventListener('error', function(err) {
        removeLoadingMessage(windowId, loadingId);
        windowData.isWaitingForResponse = false;
        addErrorMessage(windowId, 'Er is een fout opgetreden bij het verwerken van je vraag.');
        console.error('Error sending prompt:', err);
        eventSource.close();
    });
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
            chatAwayActive = false;
        }
    }
}

// Function to start the chat away process
function startChatAway() {
    console.log('Chat Away activated!');
    // No need to do anything here - the forwarding process will start
    // when the next response is received from either chat window
}

// Function to stop the chat away process
function stopChatAway() {
    console.log('Chat Away deactivated!');
    chatAwayInProgress = false;
}

// Function to forward a response from one chat window to the next
function forwardResponseToNextWindow(sourceWindowId, content) {
    // Don't forward if chat away is not active
    if (!chatAwayActive) return;
    
    // Mark that chat away is in progress to prevent infinite loops
    chatAwayInProgress = true;
    
    // Get all chat windows
    const allWindowElements = document.querySelectorAll('.chat-window');
    if (allWindowElements.length < 2) {
        chatAwayInProgress = false;
        return;
    }
    
    // Find the index of the current window
    let currentIndex = -1;
    for (let i = 0; i < allWindowElements.length; i++) {
        if (allWindowElements[i].getAttribute('data-window-id') === sourceWindowId) {
            currentIndex = i;
            break;
        }
    }
    
    if (currentIndex === -1) {
        chatAwayInProgress = false;
        return;
    }
    
    // Get the next window (wrap around to the first if we're at the last one)
    const nextIndex = (currentIndex + 1) % allWindowElements.length;
    const nextWindowElement = allWindowElements[nextIndex];
    const nextWindowId = nextWindowElement.getAttribute('data-window-id');
    
    // Don't continue if the next window is waiting for a response
    const nextWindowData = chatWindows.get(nextWindowId);
    if (!nextWindowData || nextWindowData.isWaitingForResponse) {
        chatAwayInProgress = false;
        return;
    }
    
    // Set the content as the prompt for the next window
    const nextPromptInput = nextWindowElement.querySelector('.prompt-input');
    nextPromptInput.value = content;
    
    // Use a short delay to make the interaction more natural and visible
    setTimeout(() => {
        // Send the prompt in the next window
        sendPrompt(nextWindowId);
        
        // Reset the chat away in progress flag after sending
        chatAwayInProgress = false;
    }, 1000);
}

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