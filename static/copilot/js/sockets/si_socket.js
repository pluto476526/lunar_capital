// copilot/sockets/SI_socket.js
// pkibuka@milky-way.space

document.addEventListener("DOMContentLoaded", () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const RECONNECT_DELAY = 5000;
    const MAX_RECONNECT_DELAY = 60000;

    let symbolSocket = null;
    let currentSymbol = "EURCAD"; // Default symbol

    const reconnectState = {
        attempts: 0,
        timeout: null,
    };

    function updateSymbolData(data) {
        // Update DOM with symbol-specific data
    }

    const exponentialBackoff = (attempts) =>
        Math.min(RECONNECT_DELAY * 2 ** attempts, MAX_RECONNECT_DELAY);

    const connectSymbolSocket = (symbol = null) => {
        // Clear previous reconnect timers
        clearTimeout(reconnectState.timeout);

        const asset_class = "forex";
        const wsUrl = `${wsProtocol}://${location.host}/ws/symbol-intelligence/${asset_class}/${currentSymbol}/`;
        symbolSocket = new WebSocket(wsUrl);

        symbolSocket.onopen = () => {
            console.log(`[SI] Connected to ${currentSymbol} intelligence feed`);
            reconnectState.attempts = 0;
            
            // Update UI to show connection status
            updateConnectionStatus('connected', `Connected to ${currentSymbol}`);
        };

        symbolSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log(`[SI] ${currentSymbol} data received:`, data);

                // Handle different message types
                switch(data.type) {
                    case 'connection_established':
                        console.log(`[SI] ${data.message}`);
                        break;
                    case 'symbol_intelligence':
                        updateSymbolData(data.data);
                        break;
                    default:
                        console.log('[SI] Unknown message type:', data.type);
                }
            } catch (err) {
                console.error("[SI] Error parsing message:", err);
            }
        };

        symbolSocket.onclose = () => {
            console.warn(`[SI] ${currentSymbol} connection closed, attempting to reconnect...`);
            updateConnectionStatus('disconnected', 'Connection lost - reconnecting...');
            
            reconnectState.attempts++;
            const delay = exponentialBackoff(reconnectState.attempts);
            reconnectState.timeout = setTimeout(() => connectSymbolSocket(), delay);
        };

        symbolSocket.onerror = (error) => {
            console.error("[SI] WebSocket error:", error);
            updateConnectionStatus('error', 'Connection error');
            // Let onclose handle reconnection
        };
    };

    const updateConnectionStatus = (status, message) => {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status ${status}`;
        }
    };

 

    const requestHistory = (requestId = 'default') => {
        if (symbolSocket && symbolSocket.readyState === WebSocket.OPEN) {
            symbolSocket.send(JSON.stringify({
                type: 'request_history',
                request_id: requestId,
                symbol: currentSymbol
            }));
        }
    };



    const initialize = () => {
        connectSymbolSocket();


        // Request initial history
        setTimeout(() => requestHistory('initial_load'), 1000);

        window.addEventListener("beforeunload", () => {
            if (symbolSocket) symbolSocket.close();
            clearTimeout(reconnectState.timeout);
        });
    };

    initialize();
});