// dashboard/static/js/multi-asset-intelligence.js
class MultiAssetMarketIntelligence {
    constructor() {
        this.socket = new WebSocket(
            'ws://' + window.location.host + '/ws/market-intelligence/'
        );
        
        this.assetContainers = {
            'forex': document.getElementById('forex-intelligence-container'),
            'crypto': document.getElementById('crypto-intelligence-container'),
            'stocks': document.getElementById('stocks-intelligence-container')
        };
        
        this.assetIcons = {
            'forex': 'bi-currency-exchange',
            'crypto': 'bi-currency-bitcoin',
            'stocks': 'bi-graph-up'
        };
        
        this.priorityClasses = {
            'high': 'alert-danger',
            'medium': 'alert-warning',
            'low': 'alert-info'
        };
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Handle incoming messages
        this.socket.onmessage = (e) => this.handleMessage(e);
        
        // Handle connection close
        this.socket.onclose = (e) => this.handleClose(e);
        
        // Handle connection errors
        this.socket.onerror = (e) => this.handleError(e);
    }
    
    handleMessage(e) {
        try {
            const data = JSON.parse(e.data);
            
            switch(data.type) {
                case 'market_intelligence':
                case 'immediate_update':
                    this.updateAllAssetDashboards(data.data);
                    this.updateLastUpdatedTime(data.timestamp);
                    break;
                    
                case 'preferences_updated':
                    this.showToast('Preferences updated successfully', 'success');
                    break;
                    
                case 'error':
                    this.showToast(data.message, 'danger');
                    break;
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    updateAllAssetDashboards(narrativesByAsset) {
        // Update each asset class section
        for (const [assetClass, narratives] of Object.entries(narrativesByAsset)) {
            this.updateAssetDashboard(assetClass, narratives);
        }
    }
    
    updateAssetDashboard(assetClass, narratives) {
        const container = this.assetContainers[assetClass];
        if (!container) return;
        
        // Clear existing content
        container.innerHTML = '';
        
        // Add new narratives
        if (narratives && narratives.length > 0) {
            narratives.forEach((narrative, index) => {
                const alertClass = this.priorityClasses[narrative.priority] || 'alert-secondary';
                const iconClass = this.assetIcons[assetClass] || 'bi-circle';
                
                const narrativeElement = `
                    <div class="alert ${alertClass} alert-dismissible fade show mb-3" role="alert">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h6 class="alert-heading mb-1">
                                    <i class="${iconClass} me-2"></i>
                                    ${narrative.symbol}
                                    <span class="badge bg-dark ms-2">${narrative.priority}</span>
                                </h6>
                                <p class="mb-1">${narrative.narrative}</p>
                                <small class="text-muted">
                                    ${new Date(narrative.timestamp).toLocaleTimeString()} 
                                    • Confidence: ${(narrative.confidence * 100).toFixed(0)}%
                                </small>
                            </div>
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    </div>
                `;
                
                container.innerHTML += narrativeElement;
            });
        } else {
            // No narratives available
            container.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <i class="${this.assetIcons[assetClass]} display-4 d-block mb-2"></i>
                    <p>No market intelligence available for ${assetClass}</p>
                    <small>Check back later for updates</small>
                </div>
            `;
        }
    }
    
    updateLastUpdatedTime(timestamp) {
        const timeElement = document.getElementById('last-updated-time');
        if (timeElement) {
            timeElement.textContent = new Date(timestamp).toLocaleTimeString();
        }
    }
    
    requestImmediateUpdate() {
        this.socket.send(JSON.stringify({
            type: 'request_update'
        }));
    }
    
    updatePreferences(preferences) {
        this.socket.send(JSON.stringify({
            type: 'set_preferences',
            preferences: preferences
        }));
    }
    
    handleClose(e) {
        console.log('WebSocket connection closed', e);
        this.showToast('Connection to market intelligence service lost', 'warning');
        
        // Try to reconnect after 5 seconds
        setTimeout(() => {
            this.reconnect();
        }, 5000);
    }
    
    handleError(e) {
        console.error('WebSocket error:', e);
        this.showToast('Connection error', 'danger');
    }
    
    reconnect() {
        console.log('Attempting to reconnect...');
        try {
            this.socket = new WebSocket(
                'ws://' + window.location.host + '/ws/market-intelligence/'
            );
            this.setupEventListeners();
        } catch (e) {
            console.error('Reconnection failed:', e);
        }
    }
    
    showToast(message, type = 'info') {
        // Implement toast notification system
        // You can use Bootstrap toasts or a custom implementation
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    window.marketIntelligence = new MultiAssetMarketIntelligence();
    
    // Add manual refresh button handler
    const refreshBtn = document.getElementById('refresh-intelligence');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            window.marketIntelligence.requestImmediateUpdate();
        });
    }
});
