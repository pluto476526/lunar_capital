// copilot/sockets/dash_socket.js

document.addEventListener("DOMContentLoaded", () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const RECONNECT_DELAY = 5000;
    const MAX_RECONNECT_DELAY = 60000;

    let dashSocket = null;

    const reconnectState = {
        attempts: 0,
        timeout: null,
    };


    function updateDashboard(data) {
        // --- Market Status ---
        const marketStatusEl = document.getElementById("market-status-value");
        const marketBreadthEl = document.querySelector("#market-status-card small span");
        if (marketStatusEl && data.market_status) {
            marketStatusEl.textContent = data.market_status;
        }
        if (marketBreadthEl && data.breadth_pct !== undefined) {
            marketBreadthEl.innerHTML = `+${data.breadth_pct.toFixed(1)}% <i class="bi bi-arrow-up"></i>`;
            marketBreadthEl.parentElement.lastChild.textContent = " of instruments trending up";
        }

        // --- Volatility Index ---
        const volatilityValueEl = document.getElementById("volatility-value");
        const volatilityChangeEl = document.querySelector("#volatility-card small span");
        if (volatilityValueEl && data.volatility_index !== undefined) {
            volatilityValueEl.textContent = data.volatility_index.toFixed(2);
        }
        if (volatilityChangeEl && data.volatility_change !== undefined) {
            const isPositive = data.volatility_change >= 0;
            volatilityChangeEl.innerHTML = `
                ${isPositive ? "+" : ""}${(data.volatility_change * 100).toFixed(1)}% 
                <i class="bi bi-arrow-${isPositive ? "up" : "down"}"></i>`;
            volatilityChangeEl.parentElement.lastChild.textContent = " vs. yesterday";
        }

        // --- Actionable Signals ---
        const alertsValueEl = document.getElementById("alerts-value");
        const alertsDetailsEl = document.getElementById("alerts-details");
        if (alertsValueEl && alertsDetailsEl && data.technical_breadth) {
            const { macd_bull_cross, rsi_over_70, pairs_evaluated } = data.technical_breadth;
            alertsValueEl.textContent = macd_bull_cross + rsi_over_70;
            alertsDetailsEl.innerHTML = `
                <span class="text-success">${macd_bull_cross} MACD crosses</span> | 
                <span class="text-danger">${rsi_over_70} RSI > 70</span>
                <br><small class="text-muted">Across ${pairs_evaluated} pairs</small>`;
        }

        // --- Session Activity ---
        const sessionValueEl = document.getElementById("session-activity-value");
        const sessionDetailsEl = document.getElementById("session-details");
        if (sessionValueEl && sessionDetailsEl && data.session_activity) {
            sessionValueEl.textContent = data.session_activity;
            sessionDetailsEl.innerHTML = `
                <span class="text-success">${data.current_session} 
                    <i class="bi bi-record-fill text-danger"></i>
                </span> Open`;
        }
    }


    const exponentialBackoff = (attempts) =>
        Math.min(RECONNECT_DELAY * 2 ** attempts, MAX_RECONNECT_DELAY);

    const connectDashSocket = () => {
        // Clear previous reconnect timers
        clearTimeout(reconnectState.timeout);

        const wsUrl = `${wsProtocol}://${location.host}/ws/dashboard/`;
        dashSocket = new WebSocket(wsUrl);

        dashSocket.onopen = () => {
            console.log("[DASH] Connected");
            reconnectState.attempts = 0;
        };

        dashSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("[DASH] Data received:", data);

                // TODO: update DOM / dashboard widgets here
                updateDashboard(data);
            } catch (err) {
                console.error("[DASH] Error parsing message:", err);
            }
        };

        dashSocket.onclose = () => {
            console.warn("[DASH] Connection closed, attempting to reconnect...");
            reconnectState.attempts++;
            const delay = exponentialBackoff(reconnectState.attempts);
            reconnectState.timeout = setTimeout(connectDashSocket, delay);
        };

        dashSocket.onerror = (error) => {
            console.error("[DASH] WebSocket error:", error);
            // Let onclose handle reconnection
        };
    };

    const initialize = () => {
        connectDashSocket();

        window.addEventListener("beforeunload", () => {
            if (dashSocket) dashSocket.close();
            clearTimeout(reconnectState.timeout);
        });
    };

    initialize();
});
