// Workflow automation module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

AIOntwikkelhulp.Workflow = (function() {
    
    // Workflow patterns
    const workflowPatterns = {
        issueCreation: /Ik heb issue #?(\\d+) aangemaakt voor Repo ([^\\/]+)\\/([^\\s]+)/i,
        prCreation: /Ik heb Pull Request #?(\\d+) aangemaakt voor Repo ([^\\/]+)\\/([^\\s]+)/i,
        prProcessed: /Ik heb Pull Request #?(\\d+) verwerkt en bijbehorende branche(?:([^\\s]+))? verwijderd voor Repo ([^\\/]+)\\/([^\\s.]+)\\.?/i
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
    
    // Public API
    return {
        toggleWorkflow: toggleWorkflow,
        toggleWorkflowMode: toggleWorkflowMode,
        initializeWorkflowTabs: initializeWorkflowTabs,
        monitorResponse: monitorResponse,
        autoCreateChatWindow: autoCreateChatWindow,
        autoCreateTabWindow: autoCreateTabWindow,
        autoCloseWindow: autoCloseWindow,
        configureWorkflowWindow: configureWorkflowWindow,
        showActivityIndicator: showActivityIndicator,
        hideActivityIndicator: hideActivityIndicator
    };
    
    function toggleWorkflow() {
        const workflowToggle = document.getElementById('workflow-toggle');
        const workflowActive = workflowToggle.checked;
        AIOntwikkelhulp.State.setWorkflowActive(workflowActive);
        
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
            if (!AIOntwikkelhulp.State.getWorkflowTabsInitialized()) {
                console.log('Initializing workflow tabs for the first time');
                initializeWorkflowTabs();
                AIOntwikkelhulp.State.setWorkflowTabsInitialized(true);
            } else {
                console.log('Workflow tabs already initialized, ensuring visibility');
                // Ensure all tabs are visible
                ensureTabsVisible();
            }
        } else {
            console.log('Workflow mode deactivated - switching to regular windows');
            
            // Show regular chat windows container
            chatWindowsContainer.classList.remove('d-none');
            
            // Hide workflow tabs container
            workflowTabsContainer.classList.add('d-none');
        }
    }

    function ensureTabsVisible() {
        const tabButtons = document.querySelectorAll('#workflow-tabs-container .nav-link');
        const tabPanes = document.querySelectorAll('#workflow-tabs-container .tab-pane');
        
        console.log(`Found ${tabButtons.length} tab buttons and ${tabPanes.length} tab panes`);
        
        // Ensure all tab buttons are visible
        tabButtons.forEach((button, index) => {
            button.style.display = '';
            console.log(`Tab button ${index + 1}: ${button.textContent.trim()}`);
        });
        
        // Ensure all tab panes are present
        tabPanes.forEach((pane, index) => {
            pane.style.display = '';
            console.log(`Tab pane ${index + 1}: ${pane.id}`);
        });
        
        // Re-initialize Bootstrap tabs if needed
        if (typeof bootstrap !== 'undefined') {
            tabButtons.forEach(button => {
                if (!button._bsTab) {
                    new bootstrap.Tab(button);
                }
            });
        }
    }

    function initializeWorkflowTabs() {
        console.log('Initializing workflow tabs');
        
        const tabs = {
            'issue-tab': workflowConfig.issueCreation,
            'pr-tab': workflowConfig.prCreation,
            'processed-tab': workflowConfig.prProcessed
        };
        
        // First, ensure all tab buttons and panes are visible
        ensureTabsVisible();
        
        // Then create chat windows for each tab
        for (const [tabId, config] of Object.entries(tabs)) {
            const tabPane = document.getElementById(tabId);
            const windowId = `workflow-${tabId}`;
            
            if (!tabPane) {
                console.error(`Tab pane ${tabId} not found in DOM`);
                continue;
            }
            
            // Check if window already exists
            if (document.querySelector(`[data-window-id=\"${windowId}\"]`)) {
                console.log(`Window ${windowId} already exists, skipping creation`);
                continue;
            }
            
            console.log(`Creating chat window for tab: ${tabId}`);
            
            // Create chat window in the tab
            const chatWindow = AIOntwikkelhulp.WindowManager.createChatWindowElement(windowId);
            tabPane.appendChild(chatWindow);
            
            // Initialize with workflow configuration
            AIOntwikkelhulp.WindowManager.initializeChatWindow(chatWindow);
            
            // Mark window as workflow window immediately
            const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
            if (windowData) {
                windowData.isWorkflowWindow = true;
                windowData.workflowTabId = tabId;
                console.log(`Marked window ${windowId} as workflow window for tab ${tabId}`);
            }
            
            // Configure the window with workflow settings
            setTimeout(() => {
                configureWorkflowWindow(chatWindow, config);
            }, 500);
        }
        
        // Verify all tabs are created and visible
        setTimeout(() => {
            verifyTabsCreation();
        }, 1000);
    }
    
    function verifyTabsCreation() {
        const tabButtons = document.querySelectorAll('#workflow-tabs-container .nav-link');
        const tabPanes = document.querySelectorAll('#workflow-tabs-container .tab-pane');
        const chatWindows = document.querySelectorAll('#workflow-tabs-container .chat-window');
        
        console.log('=== Workflow Tabs Verification ===');
        console.log(`Tab buttons found: ${tabButtons.length}`);
        console.log(`Tab panes found: ${tabPanes.length}`);
        console.log(`Chat windows in tabs: ${chatWindows.length}`);
        
        tabButtons.forEach((button, index) => {
            const isVisible = button.offsetParent !== null;
            console.log(`Tab ${index + 1} (${button.textContent.trim()}): ${isVisible ? 'VISIBLE' : 'HIDDEN'}`);
        });
        
        if (tabButtons.length < 3) {
            console.error('ERROR: Not all tab buttons are present!');
        }
        
        if (chatWindows.length < 3) {
            console.error('ERROR: Not all chat windows are created in tabs!');
        }
        
        console.log('=== End Verification ===');
    }
    
    function monitorResponse(windowId, content) {
        // Only monitor if workflow is active
        if (!AIOntwikkelhulp.State.getWorkflowActive()) {
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
                if (AIOntwikkelhulp.State.getWorkflowActive() && workflowConfig.tabId) {
                    // Use tab-based workflow
                    autoCreateTabWindow(prompt, workflowConfig);
                } else {
                    // Use regular window workflow
                    const newWindow = await AIOntwikkelhulp.WindowManager.addChatWindow('', true, workflowConfig);
                    const newWindowId = newWindow.getAttribute('data-window-id');

                    // Wait for configuration to complete before sending prompt
                    setTimeout(() => {
                        AIOntwikkelhulp.Network.sendPromptWithConfig(newWindowId, prompt, workflowConfig.model, workflowConfig.preset);
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
        const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
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
        const tabButton = document.querySelector(`[data-bs-target=\"#${targetTabId}\"]`);
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
            AIOntwikkelhulp.Network.sendPromptWithRetry(windowId, prompt, workflowConfig.model, workflowConfig.preset);
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
                if (typeof bootstrap !== 'undefined') {
                    const tab = new bootstrap.Tab(tabButton);
                    tab.show();
                } else {
                    // Fallback if Bootstrap is not available
                    tabButton.click();
                }
                
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
                    AIOntwikkelhulp.Network.sendPromptWithRetry(windowId, prompt, workflowConfig.model, workflowConfig.preset);
                }, 200);
            });
        }
    }

    // Activity indicator functies
    function showActivityIndicator(tabId) {
        const indicator = document.querySelector(`[data-bs-target=\"#${tabId}\"] .activity-indicator`);
        if (indicator) {
            indicator.style.display = 'inline';
            console.log(`[Activity] Showing indicator for tab ${tabId}`);
        }
    }

    function hideActivityIndicator(tabId) {
        const indicator = document.querySelector(`[data-bs-target=\"#${tabId}\"] .activity-indicator`);
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
            const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
            if (windowData) {
                windowData.workflowConfig = {
                    model: modelId,
                    preset: presetId,
                    description: description,
                    tabId: config ? config.tabId : null
                };
            }

            AIOntwikkelhulp.Formatting.addLogMessage(
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
                    AIOntwikkelhulp.Formatting.addLogMessage(
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
                                    AIOntwikkelhulp.Formatting.addLogMessage(windowId, 
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
                                    AIOntwikkelhulp.Formatting.addLogMessage(windowId, 
                                        `Waarschuwing: Preset ${presetId} niet beschikbaar, teruggevallen op ${FALLBACK_PRESET_ID}`);
                                    break;
                                }
                            }
                            
                            if (!presetSet) {
                                // Use no preset (default)
                                presetSelect.selectedIndex = 0;
                                console.warn(`[Workflow Config] ⚠ Preset ${presetId} and fallback not found, using default`);
                                AIOntwikkelhulp.Formatting.addLogMessage(windowId, 
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
        
        const windowElement = document.querySelector(`[data-window-id=\"${windowId}\"]`);
        if (!windowElement) return;
        
        // Make sure we're not closing the last window
        const allWindows = document.querySelectorAll('.chat-window');
        if (allWindows.length <= 1) {
            console.log('Cannot close the last window');
            return;
        }
        
        // Remove from global state
        AIOntwikkelhulp.State.deleteChatWindow(windowId);
        
        // Remove the element
        windowElement.remove();
        
        // Set another window as active if needed
        const remainingWindows = document.querySelectorAll('.chat-window');
        if (remainingWindows.length > 0) {
            const lastWindow = remainingWindows[remainingWindows.length - 1];
            AIOntwikkelhulp.WindowManager.setActiveWindow(lastWindow.getAttribute('data-window-id'));
        }
        
        // Update UI elements
        AIOntwikkelhulp.WindowManager.updateChatAwayToggleVisibility();
        
        // Disable remove button if only one window remains
        if (remainingWindows.length <= 1) {
            document.getElementById('remove-window-btn').disabled = true;
        }
    }
})();