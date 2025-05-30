// Global state management module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

AIOntwikkelhulp.State = (function() {
    // Private state variables
    const chatWindows = new Map();
    let chatAwayActive = false;
    let chatAwayInProgress = false;
    let lastConversationId = null;
    let workflowActive = false;
    let workflowTabsInitialized = false;
    let availablePresets = {};

    // Public API
    return {
        // Chat windows management
        getChatWindows: () => chatWindows,
        setChatWindow: (windowId, data) => chatWindows.set(windowId, data),
        getChatWindow: (windowId) => chatWindows.get(windowId),
        deleteChatWindow: (windowId) => chatWindows.delete(windowId),
        
        // Chat away state
        getChatAwayActive: () => chatAwayActive,
        setChatAwayActive: (active) => { chatAwayActive = active; },
        getChatAwayInProgress: () => chatAwayInProgress,
        setChatAwayInProgress: (inProgress) => { chatAwayInProgress = inProgress; },
        
        // Conversation management
        getLastConversationId: () => lastConversationId,
        setLastConversationId: (conversationId) => {
            if (conversationId) {
                lastConversationId = conversationId;
            }
        },
        
        // Workflow state
        getWorkflowActive: () => workflowActive,
        setWorkflowActive: (active) => { 
            workflowActive = active;
            saveWorkflowState();
        },
        getWorkflowTabsInitialized: () => workflowTabsInitialized,
        setWorkflowTabsInitialized: (initialized) => { workflowTabsInitialized = initialized; },
        
        // Presets cache
        getAvailablePresets: () => availablePresets,
        setAvailablePresets: (presets) => { availablePresets = presets; },
        
        // State persistence
        loadWorkflowState: loadWorkflowState,
        saveWorkflowState: saveWorkflowState
    };
    
    // Private functions
    function loadWorkflowState() {
        const savedState = localStorage.getItem('workflowActive');
        if (savedState !== null) {
            workflowActive = savedState === 'true';
            const workflowToggle = document.getElementById('workflow-toggle');
            if (workflowToggle) {
                workflowToggle.checked = workflowActive;
            }
            
            // Initialize workflow tabs if workflow is active
            if (workflowActive && AIOntwikkelhulp.Workflow) {
                AIOntwikkelhulp.Workflow.toggleWorkflowMode(true);
            }
        }
    }
    
    function saveWorkflowState() {
        localStorage.setItem('workflowActive', workflowActive.toString());
    }
})();