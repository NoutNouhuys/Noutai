// Main coordination and initialization module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the first window
    const firstWindow = document.querySelector('.chat-window');
    if (firstWindow) {
        AIOntwikkelhulp.WindowManager.initializeChatWindow(firstWindow);
    }
    
    // Setup control panel buttons
    setupControlPanel();
    
    // Setup theme toggle
    setupThemeToggle();
    
    // Check URL parameters to load conversations
    checkUrlParams();
    
    // Load workflow state from localStorage
    AIOntwikkelhulp.State.loadWorkflowState();

    // Voeg event listener toe voor de nieuwe knop
    const continueInNewWindowBtn = document.getElementById('continue-in-new-window-btn');
    continueInNewWindowBtn.addEventListener('click', function() {
        // Haal het laatste bericht van Claude op
        AIOntwikkelhulp.Network.fetchLastAssistantMessage()
            .then(lastMessage => {
                // Open een nieuw venster met het laatste bericht
                AIOntwikkelhulp.WindowManager.addChatWindow(lastMessage);

                // Sluit het actieve venster
                AIOntwikkelhulp.WindowManager.removeActiveWindow();
            })
            .catch(() => {
                // Als er geen bericht is, open een nieuw venster zonder prompt
                AIOntwikkelhulp.WindowManager.addChatWindow('');
                AIOntwikkelhulp.WindowManager.removeActiveWindow();
            });
    });
});

function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    if (!themeToggle) {
        console.warn('Theme toggle element not found');
        return;
    }
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    themeToggle.checked = savedTheme === 'dark';
    
    // Update icon
    updateThemeIcon(savedTheme);
    
    themeToggle.addEventListener('change', function(e) {
        const theme = e.target.checked ? 'dark' : 'light';
        html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeIcon(theme);
        
        console.log(`Theme switched to: ${theme}`);
    });
    
    console.log(`Theme toggle initialized with theme: ${savedTheme}`);
}

function updateThemeIcon(theme) {
    const themeIcons = document.querySelectorAll('.theme-icon i');
    themeIcons.forEach(icon => {
        icon.className = theme === 'dark' ? 'far fa-sun' : 'far fa-moon';
        // Update text color for non-authenticated users
        if (theme === 'dark') {
            icon.classList.remove('text-white');
            icon.classList.add('text-warning');
        } else {
            icon.classList.remove('text-warning');
            icon.classList.add('text-white');
        }
    });
}

function setupControlPanel() {
    // Add window button
    const addWindowBtn = document.getElementById('add-window-btn');
    addWindowBtn.removeEventListener('click', AIOntwikkelhulp.WindowManager.addChatWindow); // Ensures it's not duplicated
    addWindowBtn.addEventListener('click', function() {
        const conversationId = AIOntwikkelhulp.State.getLastConversationId(); // Get the current conversation ID
        if (conversationId) {
            AIOntwikkelhulp.Network.fetchLastAssistantMessage(conversationId)
                .then(lastMessage => {
                    // Check if workflow is active and configure accordingly
                    const isWorkflowWindow = AIOntwikkelhulp.State.getWorkflowActive();
                    AIOntwikkelhulp.WindowManager.addChatWindow(lastMessage, isWorkflowWindow);
                })
                .catch(() => {
                    const isWorkflowWindow = AIOntwikkelhulp.State.getWorkflowActive();
                    AIOntwikkelhulp.WindowManager.addChatWindow('', isWorkflowWindow);
                });
        } else {
            const isWorkflowWindow = AIOntwikkelhulp.State.getWorkflowActive();
            AIOntwikkelhulp.WindowManager.addChatWindow('', isWorkflowWindow);
        }
    });
    
    // Remove window button
    document.getElementById('remove-window-btn').addEventListener('click', AIOntwikkelhulp.WindowManager.removeActiveWindow);
    
    // Layout buttons
    document.getElementById('layout-single').addEventListener('click', () => AIOntwikkelhulp.WindowManager.changeLayout('single'));
    document.getElementById('layout-horizontal').addEventListener('click', () => AIOntwikkelhulp.WindowManager.changeLayout('horizontal'));
    document.getElementById('layout-grid').addEventListener('click', () => AIOntwikkelhulp.WindowManager.changeLayout('grid'));
    
    // Chat away toggle
    document.getElementById('chat-away-toggle').addEventListener('change', function(e) {
        AIOntwikkelhulp.State.setChatAwayActive(e.target.checked);
        if (AIOntwikkelhulp.State.getChatAwayActive()) {
            // Start the chat away process when activated
            AIOntwikkelhulp.ChatAway.startChatAway();
        } else {
            // Stop the chat away process when deactivated
            AIOntwikkelhulp.ChatAway.stopChatAway();
        }
    });
    
    // Workflow toggle
    document.getElementById('workflow-toggle').addEventListener('change', AIOntwikkelhulp.Workflow.toggleWorkflow);
}

function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const conversationId = urlParams.get('conversation_id');
    
    if (conversationId) {
        const firstWindow = document.querySelector('.chat-window');
        if (firstWindow) {
            const windowId = firstWindow.getAttribute('data-window-id');
            const windowData = AIOntwikkelhulp.State.getChatWindow(windowId);
            if (windowData) {
                AIOntwikkelhulp.Network.loadConversation(windowId, conversationId);
            }
        }
    }
}