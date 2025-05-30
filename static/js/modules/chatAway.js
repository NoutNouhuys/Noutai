// Chat Away functionality module
window.AIOntwikkelhulp = window.AIOntwikkelhulp || {};

AIOntwikkelhulp.ChatAway = (function() {
    
    // Public API
    return {
        startChatAway: startChatAway,
        stopChatAway: stopChatAway,
        forwardResponseToNextWindow: forwardResponseToNextWindow
    };
    
    // Function to start the chat away process
    function startChatAway() {
        console.log('Chat Away activated!');
        // No need to do anything here - the forwarding process will start
        // when the next response is received from either chat window
    }

    // Function to stop the chat away process
    function stopChatAway() {
        console.log('Chat Away deactivated!');
        AIOntwikkelhulp.State.setChatAwayInProgress(false);
    }

    // Function to forward a response from one chat window to the next
    function forwardResponseToNextWindow(sourceWindowId, content) {
        // Don't forward if chat away is not active
        if (!AIOntwikkelhulp.State.getChatAwayActive()) return;
        
        // Mark that chat away is in progress to prevent infinite loops
        AIOntwikkelhulp.State.setChatAwayInProgress(true);
        
        // Get all chat windows
        const allWindowElements = document.querySelectorAll('.chat-window');
        if (allWindowElements.length < 2) {
            AIOntwikkelhulp.State.setChatAwayInProgress(false);
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
            AIOntwikkelhulp.State.setChatAwayInProgress(false);
            return;
        }
        
        // Get the next window (wrap around to the first if we're at the last one)
        const nextIndex = (currentIndex + 1) % allWindowElements.length;
        const nextWindowElement = allWindowElements[nextIndex];
        const nextWindowId = nextWindowElement.getAttribute('data-window-id');
        
        // Don't continue if the next window is waiting for a response
        const nextWindowData = AIOntwikkelhulp.State.getChatWindow(nextWindowId);
        if (!nextWindowData || nextWindowData.isWaitingForResponse) {
            AIOntwikkelhulp.State.setChatAwayInProgress(false);
            return;
        }
        
        // Set the content as the prompt for the next window
        const nextPromptInput = nextWindowElement.querySelector('.prompt-input');
        nextPromptInput.value = content;
        
        // Use a short delay to make the interaction more natural and visible
        setTimeout(() => {
            // Send the prompt in the next window
            AIOntwikkelhulp.Network.sendPrompt(nextWindowId);
            
            // Reset the chat away in progress flag after sending
            AIOntwikkelhulp.State.setChatAwayInProgress(false);
        }, 1000);
    }
})();