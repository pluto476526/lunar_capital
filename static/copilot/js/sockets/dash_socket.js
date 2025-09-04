<!-- Add this script to your dashboard template -->
<script>
    // WebSocket connection
    const dashboardSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/dashboard/'
    );

    dashboardSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        // Update Market Status
        document.querySelector('#market-status-value').innerText = data.market_status;
        document.querySelector('#trending-up-value').innerHTML = 
            `<span class="text-success">+${data.trending_up}% <i class="bi bi-arrow-up"></i></span> of instruments trending up`;
        
        // Update Volatility Index
        document.querySelector('#volatility-index-value').innerText = data.volatility_index;
        const volChangeClass = data.volatility_change >= 0 ? 'text-danger' : 'text-success';
        const volChangeIcon = data.volatility_change >= 0 ? 'bi-arrow-up' : 'bi-arrow-down';
        document.querySelector('#volatility-change-value').innerHTML = 
            `<span class="${volChangeClass}">${Math.abs(data.volatility_change)}% <i class="bi ${volChangeIcon}"></i></span> vs. yesterday`;
        
        // Update Active Alerts
        document.querySelector('#active-alerts-value').innerText = data.active_alerts;
        const alertChangeClass = data.alerts_change >= 0 ? 'text-success' : 'text-danger';
        const alertChangeIcon = data.alerts_change >= 0 ? 'bi-arrow-up' : 'bi-arrow-down';
        document.querySelector('#alerts-change-value').innerHTML = 
            `<span class="${alertChangeClass}">${Math.abs(data.alerts_change)} <i class="bi ${alertChangeIcon}"></i></span> This week`;
        
        // Update Session Activity
        document.querySelector('#session-activity-value').innerText = data.session_activity;
        document.querySelector('#current-session-value').innerHTML = 
            `<span class="text-success">${data.current_session} <i class="bi bi-record-fill text-danger"></i></span> Open`;
    };

    dashboardSocket.onclose = function(e) {
        console.error('Dashboard socket closed unexpectedly');
        
        // Try to reconnect after 5 seconds
        setTimeout(function() {
            connectWebSocket();
        }, 5000);
    };

    // Handle connection errors
    dashboardSocket.onerror = function(err) {
        console.error('WebSocket error:', err);
    };
</script>
