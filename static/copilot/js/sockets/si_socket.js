// copilot/sockets/SI_socket.js
// pkibuka@milky-way.space


// Helper function to detect dark mode preference
function isDarkMode() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Get appropriate theme colors
function getThemeColors() {
  // return isDarkMode() ? chartTheme.dark : chartTheme.light;
    return chartTheme.dark;
}



// // Convert "BTCUSDT" -> "BTC/USDT"
function formatSymbol(asset) {
    const knownBases = ["USDT", "USD", "BTC", "ETH"];
    for (let base of knownBases) {
        if (asset.endsWith(base)) {
            const main = asset.slice(0, -base.length);
            return `${main}/${base}`;
        }
    }
    return asset;
}


function updateColor(el, value, threshold = 0) {
    // update color
    if (el) {
        if (value >= threshold) {
            el.classList.remove("text-danger");
            el.classList.add("text-success");
        } else {
            el.classList.remove("text-success");
            el.classList.add("text-danger");
        }
    }
}

function updateColor_(el, trend) {
    if (el && trend) {
        if (trend.toLowerCase() === "bullish" || trend.toLowerCase() === "strong bullish" || trend.toLowerCase() == "up") {
        el.classList.remove("text-danger");
        el.classList.add("text-success");
        } else if (trend.toLowerCase() === "bearish" || trend.toLowerCase() === "strong bearish" || trend.toLowerCase() === "down") {
        el.classList.remove("text-success");
        el.classList.add("text-danger");
        } else {
        // Neutral or unknown → muted
        el.classList.remove("text-success", "text-danger");
        el.classList.add("text-muted");
        }
    }
}

function timeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    const weeks = Math.floor(days / 7);
    if (weeks < 4) return `${weeks}w ago`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months}mo ago`;
    const years = Math.floor(days / 365);
    return `${years}y ago`;
}


function renderMainChart(element, data) {
    const priceHistory = [];
    const MAX_POINTS = 100;
    
    // Save incoming price point
    priceHistory.push({
        x: new Date(data.timestamp),
        y: data.price
    });

    if (priceHistory.length > MAX_POINTS) {
        priceHistory.shift(); // keep memory small
    }

    // Extract only the most important levels
    const pivot = data.pivot_points?.pivot;
    const support = data.support_level;
    const resistance = data.resistance_level;

    const levels = [
        { value: resistance, label: "Resistance", color: "#ef4444" },
        { value: pivot, label: "Pivot", color: "#3b82f6" },
        { value: support, label: "Support", color: "#22c55e" },
    ].filter(l => l.value !== undefined);

    // Series: Price line + level markers
    const series = [
        {
            name: "Price",
            data: [...priceHistory]
        },
        ...levels.map(l => ({
            name: l.label,
            data: priceHistory.map(p => ({ x: p.x, y: l.value })),
        }))
    ];

    const options = {
        chart: {
            type: "line",
            height: 500,
            toolbar: { show: false },
            animations: { enabled: true },
            background: "#1e293b",
            foreColor: "#e2e8f0"
        },
        stroke: {
            width: [3, ...levels.map(() => 2)],
            dashArray: [0, ...levels.map(() => 4)]
        },
        colors: ["#0ea5e9", ...levels.map(l => l.color)],
        series: series,
        xaxis: {
            type: "datetime",
            labels: { 
                datetimeUTC: false,
                style: {
                    colors: '#94a3b8'
                }
            }
        },
        yaxis: {
            decimalsInFloat: 4,
            labels: {
                formatter: val => val.toFixed(3),
                style: {
                    colors: '#94a3b8'
                }
            }
        },
        tooltip: {
            shared: true,
            x: { format: "HH:mm" },
            theme: "dark"
        },
        annotations: {
            yaxis: levels.map(l => ({
                y: l.value,
                borderColor: l.color,
                label: {
                    text: l.label + " " + l.value.toFixed(3),
                    style: {
                        background: l.color,
                        color: "#fff",
                        fontSize: "12px",
                        fontWeight: "bold"
                    }
                }
            }))
        },
        legend: { 
            show: true,
            position: 'top',
            horizontalAlign: 'right',
            labels: {
                colors: '#e2e8f0'
            }
        },
        grid: { 
            borderColor: "#374151",
            strokeDashArray: 4,
            yaxis: {
                lines: {
                    show: true
                }
            }
        }
    };

    if (element.mainChart) {
        element.mainChart.updateOptions(options);
        element.mainChart.updateSeries(series);
    } else {
        element.mainChart = new ApexCharts(element, options);
        element.mainChart.render();
    }
}


function renderPriceBarChart(element, data) {
    const colors = getThemeColors();

    const current = data.price;
    const open = data.open_price;
    const low = data.low;
    const high = data.high;

    const range = high - low || 1;
    const position = ((current - low) / range) * 100;
    const openPosition = ((open - low) / range) * 100;

    const series = [{
        name: "Price Position",
        data: [position]
    }];

    const options = {
        chart: {
            type: "bar",
            background: colors.background,
            toolbar: { show: false },
            animations: {
                enabled: true,
                easing: "easeinout",
                speed: 600
            }
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: "50%",
                borderRadius: 6
            }
        },
        colors: [current >= open ? colors.positive : colors.negative],
        dataLabels: {
            enabled: true,
            formatter: val => `${val.toFixed(1)}% | ${current.toFixed(2)}`,
            style: {
                colors: [colors.text.primary],
                fontSize: "12px",
                fontWeight: "bold"
            },
            offsetY: -6
        },
        xaxis: {
            categories: [data.symbol],
            labels: { style: { colors: colors.text.primary } },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            min: 0,
            max: 100,
            tickAmount: 4,
            labels: {
                formatter: val => {
                    if (val === 0) return `Low: ${low}`;
                    if (val === 100) return `High: ${high}`;
                    return `${val}%`;
                },
                style: { colors: colors.text.primary }
            }
        },
        grid: {
            borderColor: colors.grid,
            strokeDashArray: 4,
            xaxis: { lines: { show: false } },
            yaxis: { lines: { show: true } }
        },
        tooltip: {
            theme: isDarkMode() ? "dark" : "light",
            y: {
                formatter: () => `Price: ${current.toFixed(2)} (Low: ${low}, High: ${high})`
            }
        },
        annotations: {
            yaxis: [
                {
                    y: 100,
                    y2: 0,
                    borderColor: null,
                    fillColor: colors.grid,
                    opacity: 0.08
                },
                {
                    y: openPosition,
                    borderColor: colors.grid,
                    label: {
                        text: `Open: ${open.toFixed(2)}`,
                        style: {
                            color: colors.background,
                            background: colors.grid,
                            fontSize: "11px"
                        }
                    }
                },
                {
                    y: position,
                    borderColor: current >= open ? colors.positive : colors.negative,
                    label: {
                        style: {
                            color: colors.background,
                            background: current >= open ? colors.positive : colors.negative,
                            fontSize: "11px"
                        },
                        text: `${current.toFixed(2)}`
                    }
                }
            ]
        },
        fill: {
            type: "gradient",
            gradient: {
                shade: isDarkMode() ? "dark" : "light",
                type: "vertical",
                shadeIntensity: 0.8,
                opacityFrom: 0.95,
                opacityTo: 0.65,
                stops: [0, 100]
            }
        },
        series: series
    };

    if (element.priceBarChart) {
        element.priceBarChart.updateOptions(options, true, true);
    } else {
        element.priceBarChart = new ApexCharts(element, options);
        element.priceBarChart.render();
    }
}



function updateCryptoDash(data) {
    setTextContent(document.getElementById("crypto-symbol"), data.symbol);
    setTextContent(document.getElementById("crypto-price"), data.price);
    setTextContent(document.getElementById("crypto-open-price"), data.open);
    setTextContent(document.getElementById("crypto-market-status"), data.market_status);
    updateColor_(document.getElementById("crypto-market-status"), data.market_status);
    setTextContent(document.getElementById("crypto-current-session"), data.current_session);
    setTextContent(document.getElementById("crypto-trend-dir"), data.trend_direction);
    updateColor_(document.getElementById("crypto-trend-dir"), data.trend_direction);
    setTextContent(document.getElementById("crypto-volume"), data.volume);
    setTextContent(document.getElementById("crypto-volume-ratio"), data.volume_ratio);
    updateColor(document.getElementById("crypto-volume-ratio"), data.volume_ratio);
    setTextContent(document.getElementById("crypto-macd"), data.macd);
    setTextContent(document.getElementById("crypto-atr"), data.atr);
    setTextContent(document.getElementById("crypto-vix"), data.volatility_index);
    setTextContent(document.getElementById("crypto-obv"), data.obv);
    setTextContent(document.getElementById("crypto-support"), data.support_level);
    setTextContent(document.getElementById("crypto-resistance"), data.resistance_level);
    setTextContent(document.getElementById("crypto-s1"), data.pivot_points.s1);
    setTextContent(document.getElementById("crypto-s2"), data.pivot_points.s2);
    setTextContent(document.getElementById("crypto-s3"), data.pivot_points.s3);
    setTextContent(document.getElementById("crypto-r1"), data.pivot_points.r1);
    setTextContent(document.getElementById("crypto-r2"), data.pivot_points.r2);
    setTextContent(document.getElementById("crypto-r3"), data.pivot_points.r3);
    setTextContent(document.getElementById("crypto-pivot"), data.pivot_points.pivot);
    setTextContent(document.getElementById("crypto-upper-bb"), data.bollinger_upper);
    setTextContent(document.getElementById("crypto-middle-bb"), data.bollinger_middle);
    setTextContent(document.getElementById("crypto-lower-bb"), data.bollinger_lower);
    setTextContent(document.getElementById("crypto-sma5"), data.sma_5);
    setTextContent(document.getElementById("crypto-sma10"), data.sma_10);
    setTextContent(document.getElementById("crypto-sma20"), data.sma_20);
    setTextContent(document.getElementById("crypto-vwap"), data.vwap);
    setTextContent(document.getElementById("crypto-proximity"), data.price_proximity);
    setTextContent(document.getElementById("crypto-opening-range-high"), data.opening_range_high);
    setTextContent(document.getElementById("crypto-opening-range-low"), data.opening_range_low);
    setTextContent(document.getElementById("crypto-or-breakout"), data.or_breakout);
    updateColor_(document.getElementById("crypto-or-breakout"), data.or_breakout);
    setTextContent(document.getElementById("crypto-gap-pct"), data.gap_pct);
    setTextContent(document.getElementById("crypto-intraday-range-pct"), data.intraday_range_pct);
    setTextContent(document.getElementById("crypto-atr-ratio"), data.atr_ratio);
    setTextContent(document.getElementById("crypto-volume-ratio2"), data.volume_ratio);
    setTextContent(document.getElementById("crypto-volume-spike"), data.volume_spike);
    updateColor(document.getElementById("crypto-volume-spike"), data.volume_spike);
    setTextContent(document.getElementById("crypto-macd2"), data.macd);
    setTextContent(document.getElementById("crypto-macd-signal"), data.macd_signal);
    setTextContent(document.getElementById("crypto-macd-histogram"), data.macd_histogram);
    setTextContent(document.getElementById("timestamp"), timeAgo(data.timestamp));


    const changeEl = document.getElementById("crypto-change");
    if (changeEl) {
        const overallChange = data.price_change_pct.toFixed(2) + "%";
        const intradayChange = data.intraday_change_pct.toFixed(2) + "% Today";

        changeEl.textContent = `${overallChange} (${intradayChange})`;
        updateColor(changeEl, data.price_change_pct);
    }

    // crypto rsi
    setTextContent(document.getElementById("crypto-rsi"), data.rsi);
    rsiProgress = document.getElementById("crypto-rsi-bar");
    if (rsiProgress) rsiProgress.style.width = data.rsi + "%";
    updateColor(rsiProgress, data.rsi, 50);

    // adx
    setTextContent(document.getElementById("crypto-adx"), data.adx);
    adxProgress = document.getElementById("crypto-adx-bar");
    if (adxProgress) adxProgress.style.width = data.adx + "%";

    // Trend Srength
    setTextContent(document.getElementById("crypto-trend-strength"), data.trend_strength);
    trendProgress = document.getElementById("crypto-trend-bar");
    if (trendProgress) trendProgress.style.width = (data.trend_strength * 100) + "%";
    updateColor(trendProgress, data.trend_strength);



    // Price mini line chart
    priceBarChartEl = document.getElementById("mini-line-chart");
    if (priceBarChartEl) renderPriceBarChart(priceBarChartEl, data);

    // Main Chart
    mainChartEl = document.getElementById("crypto-main-chart");
    if (mainChartEl) renderMainChart(mainChartEl, data);
}











document.addEventListener("DOMContentLoaded", () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const RECONNECT_DELAY = 5000;
    const MAX_RECONNECT_DELAY = 60000;
    let symbolSocket = null;
    
    const reconnectState = {
        attempts: 0,
        timeout: null,
    };

    const exponentialBackoff = (attempts) =>
        Math.min(RECONNECT_DELAY * 2 ** attempts, MAX_RECONNECT_DELAY);
   
    const connectSymbolSocket = (symbol = null) => {
        // Clear previous reconnect timers
        clearTimeout(reconnectState.timeout);

        // const asset_class = "forex";
        const wsUrl = `${wsProtocol}://${location.host}/ws/symbol-data/EURCAD/`;
        symbolSocket = new WebSocket(wsUrl);

        symbolSocket.onopen = () => {
            console.log(`[SI] Connected to intelligence feed`);
            reconnectState.attempts = 0;
            
            // Update UI to show connection status
            updateConnectionStatus('connected', `Connected`);
            //requestAssetData(symbol, symbolSocket);

            // Get and convert path ie. "BTCUSDT" -> "BTC/USDT"
            const path = window.location.pathname;
            const parts = path.split("/").filter(Boolean);
            // ["co-pilot", "crypto", "BTCUSDT"]

            const asset = parts[parts.length - 1];
            const symbol = formatSymbol(asset);
            console.log("symbol: ", symbol);


            symbolSocket.send(JSON.stringify({
                type: 'request_symbol_details',
                symbol: symbol
            }));
        };

        symbolSocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Handle different message types
                switch(data.type) {
                    case 'connection_established':
                        console.log(`[SI] ${data.message}`);
                        break;
                    case 'symbol_intelligence':
                        console.log("symbol data >>: ", data.payload);
                        updateCryptoDash(data.payload);
                        renderAssetDetails(data.payload);
                        break;
                    default:
                        console.log('[SI] Unknown message type:', data.type);
                }
            } catch (err) {
                console.error("[SI] Error parsing message:", err);
            }
        };

        symbolSocket.onclose = () => {
            console.warn("[SI]connection closed, attempting to reconnect...");
            updateConnectionStatus('disconnected', 'Connection lost - reconnecting...');
            
            reconnectState.attempts++;
            const delay = exponentialBackoff(reconnectState.attempts);
            reconnectState.timeout = setTimeout(() => connectSymbolSocket(), delay);
        };

        symbolSocket.onerror = (error) => {
            console.error("[SI] WebSocket error:", error);
            updateConnectionStatus('error', 'Connection error');
        };
    };

    const updateConnectionStatus = (status, message) => {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status ${status}`;
        }
    };

 

    


    const initialize = () => {
        connectSymbolSocket();

        window.addEventListener("beforeunload", () => {
            if (symbolSocket) symbolSocket.close();
            clearTimeout(reconnectState.timeout);
        });
    };

    initialize();
    window.symbolSocket = symbolSocket;
});