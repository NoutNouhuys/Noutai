/**
 * Platform Selector Module
 * 
 * Handles platform selection UI and communication with the backend
 * for multi-platform Git repository support (GitHub and Bitbucket).
 */

class PlatformSelector {
    constructor() {
        this.currentPlatform = 'auto';
        this.availablePlatforms = [];
        this.connectionStatus = {};
        this.initialized = false;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    async init() {
        console.log('[Platform Selector] Initializing...');
        
        try {
            // Create platform selector UI
            this.createPlatformSelectorUI();
            
            // Load platform status
            await this.loadPlatformStatus();
            
            // Set up event listeners
            this.setupEventListeners();
            
            this.initialized = true;
            console.log('[Platform Selector] Initialized successfully');
            
        } catch (error) {
            console.error('[Platform Selector] Initialization failed:', error);
        }
    }
    
    createPlatformSelectorUI() {
        // Find the control panel or create one
        let controlPanel = document.querySelector('.control-panel');
        if (!controlPanel) {
            console.warn('[Platform Selector] Control panel not found, creating one');
            controlPanel = document.createElement('div');
            controlPanel.className = 'control-panel mb-3';
            document.body.insertBefore(controlPanel, document.body.firstChild);
        }
        
        // Create platform selector container
        const platformContainer = document.createElement('div');
        platformContainer.className = 'platform-selector-container d-flex align-items-center gap-3 mb-2';
        platformContainer.innerHTML = `
            <div class="platform-selector-group">
                <label for="platform-select" class="form-label mb-0">
                    <i class="fab fa-git-alt me-1"></i> Platform:
                </label>
                <select id="platform-select" class="form-select form-select-sm d-inline-block" style="width: auto;">
                    <option value="auto">Auto-detect</option>
                    <option value="github">GitHub</option>
                    <option value="bitbucket">Bitbucket</option>
                </select>
            </div>
            
            <div class="platform-status-group">
                <div id="platform-status-indicators" class="d-flex gap-2">
                    <!-- Status indicators will be populated here -->
                </div>
            </div>
            
            <div class="platform-actions-group">
                <button id="refresh-platforms-btn" class="btn btn-sm btn-outline-secondary" title="Refresh platform connections">
                    <i class="fas fa-sync-alt"></i>
                </button>
            </div>
        `;
        
        // Insert at the beginning of the control panel
        controlPanel.insertBefore(platformContainer, controlPanel.firstChild);
    }
    
    async loadPlatformStatus() {
        try {
            console.log('[Platform Selector] Loading platform status...');
            
            const response = await fetch('/api/platform/status', {
                headers: getAPIHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.connectionStatus = data.connection_status || {};
                this.availablePlatforms = data.available_platforms || [];
                this.currentPlatform = data.active_platform || 'auto';
                
                console.log('[Platform Selector] Status loaded:', {
                    connectionStatus: this.connectionStatus,
                    availablePlatforms: this.availablePlatforms,
                    currentPlatform: this.currentPlatform
                });
                
                this.updateUI();
            } else {
                console.error('[Platform Selector] Failed to load status:', data.error);
                this.showError('Failed to load platform status');
            }
            
        } catch (error) {
            console.error('[Platform Selector] Error loading platform status:', error);
            this.showError('Error connecting to platform service');
        }
    }
    
    updateUI() {
        this.updatePlatformSelect();
        this.updateStatusIndicators();
    }
    
    updatePlatformSelect() {
        const platformSelect = document.getElementById('platform-select');
        if (!platformSelect) return;
        
        // Set current selection
        platformSelect.value = this.currentPlatform;
        
        // Enable/disable options based on availability
        const options = platformSelect.querySelectorAll('option');
        options.forEach(option => {
            const platform = option.value;
            
            if (platform === 'auto') {
                option.disabled = false;
                return;
            }
            
            const isConnected = this.connectionStatus[platform] === true;
            option.disabled = !isConnected;
            
            // Update option text to show status
            const baseText = option.textContent.split(' (')[0]; // Remove existing status
            if (isConnected) {
                option.textContent = `${baseText} (Connected)`;
            } else {
                option.textContent = `${baseText} (Disconnected)`;
            }
        });
    }
    
    updateStatusIndicators() {
        const statusContainer = document.getElementById('platform-status-indicators');
        if (!statusContainer) return;
        
        statusContainer.innerHTML = '';
        
        // Create status indicators for each platform
        const platforms = ['github', 'bitbucket'];
        
        platforms.forEach(platform => {
            const isConnected = this.connectionStatus[platform] === true;
            const indicator = document.createElement('div');
            indicator.className = `platform-status-indicator ${platform}`;
            indicator.title = `${platform.charAt(0).toUpperCase() + platform.slice(1)}: ${isConnected ? 'Connected' : 'Disconnected'}`;
            
            const icon = this.getPlatformIcon(platform);
            const statusClass = isConnected ? 'connected' : 'disconnected';
            
            indicator.innerHTML = `
                <i class="${icon} platform-icon"></i>
                <span class="status-dot ${statusClass}"></span>
            `;
            
            statusContainer.appendChild(indicator);
        });
        
        // Add active platform indicator if not auto
        if (this.currentPlatform !== 'auto') {
            const activeIndicator = document.createElement('div');
            activeIndicator.className = 'active-platform-indicator';
            activeIndicator.title = `Active platform: ${this.currentPlatform}`;
            activeIndicator.innerHTML = `
                <i class="fas fa-arrow-right me-1"></i>
                <i class="${this.getPlatformIcon(this.currentPlatform)}"></i>
            `;
            statusContainer.appendChild(activeIndicator);
        }
    }
    
    getPlatformIcon(platform) {
        const icons = {
            github: 'fab fa-github',
            bitbucket: 'fab fa-bitbucket'
        };
        return icons[platform] || 'fas fa-code-branch';
    }
    
    setupEventListeners() {
        // Platform selection change
        const platformSelect = document.getElementById('platform-select');
        if (platformSelect) {
            platformSelect.addEventListener('change', (e) => {
                this.changePlatform(e.target.value);
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refresh-platforms-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshPlatforms();
            });
        }
    }
    
    async changePlatform(newPlatform) {
        if (newPlatform === this.currentPlatform) return;
        
        try {
            console.log(`[Platform Selector] Changing platform to: ${newPlatform}`);
            
            // Show loading state
            this.setLoadingState(true);
            
            const response = await fetch('/api/platform/set-active', {
                method: 'POST',
                headers: getAPIHeaders(),
                body: JSON.stringify({
                    platform: newPlatform
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPlatform = newPlatform;
                this.updateUI();
                this.showSuccess(`Platform changed to ${newPlatform}`);
                
                // Notify other components about platform change
                this.notifyPlatformChange(newPlatform);
                
            } else {
                throw new Error(data.error || 'Failed to change platform');
            }
            
        } catch (error) {
            console.error('[Platform Selector] Error changing platform:', error);
            this.showError(`Failed to change platform: ${error.message}`);
            
            // Revert selection
            const platformSelect = document.getElementById('platform-select');
            if (platformSelect) {
                platformSelect.value = this.currentPlatform;
            }
        } finally {
            this.setLoadingState(false);
        }
    }
    
    async refreshPlatforms() {
        try {
            console.log('[Platform Selector] Refreshing platform connections...');
            
            // Show loading state
            this.setLoadingState(true);
            
            const response = await fetch('/api/platform/refresh', {
                method: 'POST',
                headers: getAPIHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.connectionStatus = data.connection_status || {};
                this.availablePlatforms = data.available_platforms || [];
                this.updateUI();
                this.showSuccess('Platform connections refreshed');
            } else {
                throw new Error(data.error || 'Failed to refresh platforms');
            }
            
        } catch (error) {
            console.error('[Platform Selector] Error refreshing platforms:', error);
            this.showError(`Failed to refresh platforms: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }
    
    setLoadingState(loading) {
        const refreshBtn = document.getElementById('refresh-platforms-btn');
        const platformSelect = document.getElementById('platform-select');
        
        if (refreshBtn) {
            refreshBtn.disabled = loading;
            const icon = refreshBtn.querySelector('i');
            if (icon) {
                if (loading) {
                    icon.className = 'fas fa-spinner fa-spin';
                } else {
                    icon.className = 'fas fa-sync-alt';
                }
            }
        }
        
        if (platformSelect) {
            platformSelect.disabled = loading;
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `platform-notification alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    notifyPlatformChange(newPlatform) {
        // Dispatch custom event for other components to listen to
        const event = new CustomEvent('platformChanged', {
            detail: {
                platform: newPlatform,
                connectionStatus: this.connectionStatus,
                availablePlatforms: this.availablePlatforms
            }
        });
        
        document.dispatchEvent(event);
    }
    
    // Public API methods
    getCurrentPlatform() {
        return this.currentPlatform;
    }
    
    getConnectionStatus() {
        return { ...this.connectionStatus };
    }
    
    getAvailablePlatforms() {
        return [...this.availablePlatforms];
    }
    
    isConnected(platform) {
        return this.connectionStatus[platform] === true;
    }
}

// Create global instance
window.PlatformSelector = new PlatformSelector();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PlatformSelector;
}