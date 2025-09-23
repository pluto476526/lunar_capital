// copilot/sockets/dash_socket.js

let fxCorrelationEl, fxKeyLevelEl, stockNarrativeHeadlineEl, stockNarrativeEl;
let stockNarrativeMetaEl, stockCorrelationEl, cryptoCorrelationEl;
let cryptoBreadthTrendEl, dominanceEl, VolumeChartEl;


// Function to load asset details
function loadAssetDetails(asset_class, symbol) {
    const detailsContainer = document.getElementById(`${asset_class}-asset-details`);
    detailsContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading ${symbol} details...</p>
        </div>
    `;

    if (window.symbolSocket && window.symbolSocket.readyState === WebSocket.OPEN) {
        window.symbolSocket.send(JSON.stringify({
            type: "request_symbol_details",
            asset_class: asset_class,
            symbol: symbol
        }));
    } else {
        console.warn("Symbol socket not connected.");
    }
}

function renderAssetDetails(asset_class, data) {
    const detailsContainer = document.getElementById(`${asset_class}-asset-details`);
    if (!detailsContainer) return;

    // Helper function to determine trend color
    const getTrendColor = (direction) => {
        const colors = {
            bullish: 'success',
            bearish: 'danger',
            neutral: 'info'
        };
        return colors[direction] || 'secondary';
    };

    // Format numbers with commas
    const formatNumber = (num) => {
        return num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 4
        });
    };

    detailsContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0">${data.symbol} Overview</h6>
            <span class="badge bg-${getTrendColor(data.trend_direction)}">
                ${data.trend_direction.toUpperCase()}
            </span>
        </div>
        
        <div class="row">
            <!-- Price and Volume Section -->
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title border-bottom pb-2">Price & Volume</h6>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Price:</span>
                            <strong>${formatNumber(data.price)}</strong>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span>24h Change:</span>
                            <span class="${data.price_change_pct >= 0 ? 'text-success' : 'text-danger'}">
                                ${data.price_change_pct >= 0 ? '+' : ''}${data.price_change_pct.toFixed(2)}%
                            </span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Volume:</span>
                            <strong>${data.volume.toLocaleString()}</strong>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span>VWAP:</span>
                            <strong>${data.vwap.toFixed(2)}</strong>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Technical Indicators -->
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title border-bottom pb-2">Technical Indicators</h6>
                        
                        <div class="mb-2">
                            <div class="d-flex justify-content-between">
                                <span>RSI:</span>
                                <strong>${data.rsi.toFixed(2)}</strong>
                            </div>
                            <div class="progress mt-1" style="height:6px;">
                                <div class="progress-bar ${data.rsi > 70 ? 'bg-danger' : data.rsi < 30 ? 'bg-primary' : 'bg-success'}" 
                                     role="progressbar" style="width:${Math.min(data.rsi, 100)}%">
                                </div>
                            </div>
                            <small class="text-muted">
                                ${data.rsi > 70 ? 'Overbought' : data.rsi < 30 ? 'Oversold' : 'Neutral'}
                            </small>
                        </div>
                        
                        <div class="mb-2">
                            <div class="d-flex justify-content-between">
                                <span>Trend Strength:</span>
                                <strong>${(data.trend_strength * 100).toFixed(1)}%</strong>
                            </div>
                            <div class="progress mt-1" style="height:6px;">
                                <div class="progress-bar bg-info" role="progressbar" 
                                     style="width:${Math.min(data.trend_strength * 100, 100)}%">
                                </div>
                            </div>
                        </div>
                        
                        <div class="d-flex justify-content-between mt-3">
                            <span>Market Status:</span>
                            <strong class="text-capitalize">${data.market_status}</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <!-- Support & Resistance -->
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title border-bottom pb-2">Support & Resistance</h6>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Support:</span>
                            <strong>${data.support_level}</strong>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span>Resistance:</span>
                            <strong>${data.resistance_level}</strong>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Volatility -->
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title border-bottom pb-2">Volatility</h6>
                        <div class="d-flex justify-content-between mb-2">
                            <span>ATR:</span>
                            <strong>${data.atr.toFixed(2)}</strong>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span>Volatility Index:</span>
                            <strong>${data.volatility_index}</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Volume Activity -->
        <div class="card mb-3">
            <div class="card-body">
                <h6 class="card-title border-bottom pb-2">Volume Activity</h6>
                <div class="d-flex justify-content-between mb-2">
                    <span>Volume Ratio:</span>
                    <strong>${(data.volume_ratio * 100).toFixed(1)}%</strong>
                </div>
                <div class="progress mt-1" style="height:6px;">
                    <div class="progress-bar bg-warning" role="progressbar" 
                         style="width:${Math.min(data.volume_ratio * 100, 100)}%">
                    </div>
                </div>
                <small class="text-muted">
                    ${data.volume_ratio > 1 ? 'Above average' : 'Below average'} volume
                </small>
            </div>
        </div>
        
        <!-- View Full Analysis Button -->
        <div class="d-grid">
            <button class="btn btn-primary" onclick="viewFullAnalysis('${data.symbol}')">
                <i class="fas fa-chart-line me-2"></i>View Full Analysis
            </button>
        </div>
    `;
}

// Handle button click
function viewFullAnalysis(symbol) {
    const cleanSymbol = symbol.replace("/", "");
    const currentPath = window.location.pathname.replace(/\/$/, ""); // remove trailing slash
    const newPath = `${currentPath}/${cleanSymbol}/`;
    const targetUrl = `${window.location.origin}${newPath}`;
    window.location.href = targetUrl;
}




// Helper functions for common operations
function setTextContent(element, value) {
    if (element && value !== undefined) {
        element.textContent = value;
    }
}

function updateChangeElement(element, value, threshold = 0, multiplier = 1) {
    if (element && value !== undefined) {
        const isPositive = value >= threshold;
        const displayValue = (value * multiplier).toFixed(1);
        element.innerHTML = `
            ${isPositive && value > 0 ? "+" : ""}${displayValue}% 
            <i class="bi bi-arrow-${isPositive ? "up text-success" : "down text-danger"}"></i>`;
    }
}


function updateForexDashboard(data) {
    // Market Status
    setTextContent(document.getElementById("fx-market-status-value"), data.market_status);
    const marketBreadthEl = document.querySelector("#fx-market-status-card small span");
    updateChangeElement(marketBreadthEl, data.breadth_pct, 50, 1);
    // marketBreadthEl.parentElement.lastChild.textContent = " of analyzed pairs";

    // Volatility Index
    setTextContent(document.getElementById("fx-volatility-value"), 
                  data.volatility_index?.toFixed(2));
    
    updateChangeElement(
        document.querySelector("#fx-volatility-card small span"),
        data.volatility_change,
        0,
        100
    );

    // Session Activity
    setTextContent(document.getElementById("fx-current-session"), data.current_session);
    setTextContent(document.getElementById("fx-session-activity"), data.session_activity);

    // Market Liquidity
    setTextContent(document.getElementById("fx-liquidity-status"), data.market_liquidity.liquidity_status);
    setTextContent(document.getElementById("fx-volume-ratio"), data.market_liquidity.liquidity_score);

    // Market Intelligence - Narrative
    setTextContent(document.getElementById("fx-narrative-headline"), data.narrative.headline);
    setTextContent(document.getElementById("fx-narrative-desc"), data.narrative.narrative);

    const newsListEl = document.getElementById("fx-news");
    if (data.news && newsListEl) {
        const topNews = data.news.slice(0, 5); // first 5

        // clear old news
        newsListEl.innerHTML = "";

        topNews.forEach(item => {
        const newsItem = document.createElement("a");
        newsItem.href = item.url || "#";
        newsItem.target = "_blank"; // open in new tab
        newsItem.className = "list-group-item list-group-item-action";
        newsItem.innerHTML = `
          <div class="d-flex w-100 justify-content-between">
            <h6 class="mb-1">${item.title}</h6>
            <small>${new Date(item.publishedAt).toLocaleString()}</small>
          </div>
          <p class="mb-1">${item.description || "Visit website to view full item."}</p>
        `;

        newsListEl.appendChild(newsItem);
        });
    }

    // Currency Pair Correlation Matrix
    fxCorrelationEl = document.getElementById("fx-correlation-matrix");
    if (fxCorrelationEl) renderCorrelationMatrix(fxCorrelationEl, data.correlation_matrix);

    // Market Makers
    const gainersEl = document.getElementById("fx-top-gainers");
    const losersEl = document.getElementById("fx-top-losers");
    if (gainersEl) {
        const { gainers, losers } = data.top_movers;

        /// Helper to generate table rows
        function createListItem(item, isGainer = true) {
            return `
                <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                <span>${item.symbol}</span>
                <span>${item.latest.toFixed(2)}</span>
                <span class="badge ${isGainer ? 'bg-success' : 'bg-danger'}">
                    ${item.change_pct >= 0 ? '+' : ''}${item.change_pct.toFixed(2)}%
                </span>
                </li>
            `;
        }

        // Update tables
        gainersEl.innerHTML = gainers.map(item => createListItem(item, true)).join("");
        losersEl.innerHTML = losers.map(item => createListItem(item, false)).join("");
    }

    // Tech Indicators Accordion
    const fxIndicatorsEl = document.getElementById("fx-tech-indicators");
    if (fxIndicatorsEl) {
        fxIndicatorsEl.innerHTML = "";

        const { counts, symbols } = data.technical_breadth;
        const total = counts.symbols_evaluated || 0;

        const indicatorsMap = [
            { label: "RSI Above 60", countKey: "rsi_over_60", symbolKey: "rsi_over" },
            { label: "MACD Bullish Cross", countKey: "macd_bull_cross", symbolKey: "macd_bull_cross" },
            { label: "Above 20-Day MA", countKey: "above_ma20", symbolKey: "above_ma20" },
            { label: "Above 50-Day MA", countKey: "above_ma50", symbolKey: "above_ma50" },
            { label: "Above 200-Day MA", countKey: "above_ma200", symbolKey: "above_ma200" },
            { label: "Above VWAP", countKey: "above_vwap", symbolKey: "above_vwap" },
            { label: "High Volume", countKey: "high_volume", symbolKey: "high_volume" }
        ];

        indicatorsMap.forEach(({ label, countKey, symbolKey }, idx) => {
            const id = `symbols-${countKey}-${idx}`;

            const li = document.createElement("li");
            li.className = "list-group-item px-0";

            const symbolList = (symbols[symbolKey] && symbols[symbolKey].length > 0)
                ? `<ul class="mb-0 ps-3">${symbols[symbolKey].map(s => `<li>${s}</li>`).join("")}</ul>`
                : "<em class='text-muted'>None</em>";

            li.innerHTML = `
                <div class="d-flex justify-content-between align-items-center" 
                     data-bs-toggle="collapse" 
                     data-bs-target="#${id}" 
                     style="cursor:pointer;">
                    ${label}
                    <span class="badge bg-secondary rounded-pill">${counts[countKey] || 0}/${total}</span>
                </div>
                <div id="${id}" class="collapse mt-2">
                    <small class="text-muted">
                        ${symbolList}
                    </small>
                </div>
            `;

            fxIndicatorsEl.appendChild(li);
        });
    }

    

    // Breadth Chart
    fxBreadthTrendEl = document.getElementById("fx-breadth-trend");
    if (fxBreadthTrendEl) renderBreadthChart(fxBreadthTrendEl, data.breadth_series);

    // Pairs List
    const fxListEl = document.getElementById("fx-pairs-list");    
    if (fxListEl) {
        const assets = data.symbols;
        const searchEl = document.getElementById("fx-search");

        // Function to render the list
        function renderAssets(data) {
            if (!data) return;
            fxListEl.innerHTML = '';
            const list = data.slice(0, 10);

            list.forEach(asset => {
                const item = document.createElement("li");
                item.className = "list-group-item d-flex align-items-center gap-2";
                item.setAttribute("data-symbol", asset.symbol);
                item.style.cursor = "pointer";
                item.style.userSelect = "none";

                item.innerHTML = `
                    <div>
                        <img src="/static/images/${asset.symbol.split("/")[0].toLowerCase()}.png" width="20" height="20">
                    </div>
                    <div>${asset.name} (${asset.symbol})</div>
                    <div class="ms-auto">
                        <span>${asset.price.toFixed(2)}</span>
                    </div>
                `;

                item.addEventListener("click", () => loadAssetDetails("fx", asset.symbol));
                fxListEl.appendChild(item);
            });
        }

        // Initial render
        renderAssets(assets);

        // Search filter (case-insensitive, partial match)
        if (searchEl) {
            searchEl.addEventListener("input", () => {
                const query = searchEl.value.trim().toLowerCase();
                const filtered = assets.filter(asset =>
                    asset.symbol.toLowerCase().includes(query) ||
                    asset.name.toLowerCase().includes(query)
                );
                renderAssets(filtered);
            });
        }
    }
}

function updateStocksDashboard(data) {
    // Market Status
    setTextContent(document.getElementById("stock-market-status-value"), data.market_status);
    
    const marketBreadthEl = document.getElementById("stock-market-breadth");
    if (data.breadth_pct) {
        updateChangeElement(marketBreadthEl, data.breadth_pct, 50, 1);
        // marketBreadthEl.parentElement.lastChild.textContent = " of analyzed instruments";
    }

    // Volatility Index
    setTextContent(document.getElementById("stock-volatility-value"), data.volatility_index?.toFixed(2));
    
    updateChangeElement(document.querySelector("#stock-volatility-card small span"),data.volatility_change, 0, 100);

    // Market Liquidity
    if (data.market_liquidity) {
        setTextContent(document.getElementById("stock-liquidity-score"), data.market_liquidity.liquidity_score);
        setTextContent(document.getElementById("stock-liquidity-status"), data.market_liquidity.liquidity_status);
    }

    // Session Activity
    setTextContent(document.getElementById("stock-current-session"), data.current_session);
    setTextContent(document.getElementById("stock-session-activity"), data.session_activity);

    // Sector Performance
    const sectorPerformanceEl = document.getElementById("sector-performance-chart");
    if (sectorPerformanceEl) {
        renderSectorPerformanceTreemap(sectorPerformanceEl, data.narrative.sector_analysis.all_sectors);
    }

    // Market Narrative
    stockNarrativeHeadlineEl = document.getElementById("stock-market-narrative-headline");
    stockNarrativeEl = document.getElementById("stock-market-narrative");
    stockNarrativeMetaEl = document.getElementById("stock_market-narrative-meta");
    if (stockNarrativeEl) {
        setTextContent(stockNarrativeHeadlineEl, data.narrative.headline);
        setTextContent(stockNarrativeEl, data.narrative.narrative);
        setTextContent(stockNarrativeMetaEl, new Date(data.narrative.generated_at).toLocaleString());
    }

    // News
    const newsListEl = document.getElementById("news-list");
    if (newsListEl) {
        const topNews = data.news.slice(0, 5); // first 5

        // clear old news
        newsListEl.innerHTML = "";

        topNews.forEach(item => {
        const newsItem = document.createElement("a");
        newsItem.href = item.url || "#";
        newsItem.target = "_blank"; // open in new tab
        newsItem.className = "list-group-item list-group-item-action";

        newsItem.innerHTML = `
          <div class="d-flex w-100 justify-content-between">
            <h6 class="mb-1">${item.title || "Untitled"}</h6>
            <small>${new Date(item.publishedAt).toLocaleString()}</small>
          </div>
          <p class="mb-1">${item.description || "Visit website to view full item."}</p>
        `;

        newsListEl.appendChild(newsItem);
      });
    }

    stockCorrelationEl = document.getElementById("stock-correlation-matrix");
    if (stockCorrelationEl) renderStockCorrelationMatrix(stockCorrelationEl, data.correlation_matrix);

    // Index Returns Chart
    const indexPerformanceEl = document.getElementById("index-performance-chart");
    if (indexPerformanceEl) renderIndexPerformanceChart(indexPerformanceEl, data.index_returns);

    const gainersEl = document.getElementById("stock-top-gainers-body");
    const losersEl = document.getElementById("stock-top-losers-body");
    if (gainersEl) {
        const { gainers, losers } = data.top_movers;

        /// Helper to generate table rows
        function createRow(item, isGainer = true) {
            return `
              <tr>
                <td>${item.symbol}</td>
                <td>${item.latest ? item.latest.toFixed(2) : 'N/A'}</td>
                <td><span class="badge ${isGainer ? 'bg-success' : 'bg-danger'}">
                    ${item.change_pct >= 0 ? '+' : ''}${item.change_pct.toFixed(2)}%
                </span></td>
              </tr>
            `;
        }

        // Update tables
        gainersEl.innerHTML = gainers.map(item => createRow(item, true)).join("");
        losersEl.innerHTML = losers.map(item => createRow(item, false)).join("");
    }


    // Tech Indicators Accordion
    // Tech Indicators Accordion
    const stockIndicatorsEl = document.getElementById("stocks-tech-indicators");
    if (stockIndicatorsEl) {
        stockIndicatorsEl.innerHTML = "";

  
        const { counts, symbols } = data.technical_breadth;
        const total = counts.symbols_evaluated || 0;

        const indicatorsMap = [
            { label: "RSI Above 70", countKey: "rsi_over_70", symbolKey: "rsi_over" },
            { label: "MACD Bullish Cross", countKey: "macd_bull_cross", symbolKey: "macd_bull_cross" },
            { label: "Above 20-Day MA", countKey: "above_ma20", symbolKey: "above_ma20" },
            { label: "Above 50-Day MA", countKey: "above_ma50", symbolKey: "above_ma50" },
            { label: "Above 200-Day MA", countKey: "above_ma200", symbolKey: "above_ma200" },
            { label: "Above VWAP", countKey: "above_vwap", symbolKey: "above_vwap" },
            { label: "High Volume", countKey: "high_volume", symbolKey: "high_volume" }
        ];

        indicatorsMap.forEach(({ label, countKey, symbolKey }, idx) => {
            const id = `symbols-${countKey}-${idx}`;

            const li = document.createElement("li");
            li.className = "list-group-item px-0";

            const symbolList = (symbols[symbolKey] && symbols[symbolKey].length > 0)
                ? `<ul class="mb-0 ps-3">${symbols[symbolKey].map(s => `<li>${s}</li>`).join("")}</ul>`
                : "<em class='text-muted'>None</em>";

            li.innerHTML = `
                <div class="d-flex justify-content-between align-items-center" 
                     data-bs-toggle="collapse" 
                     data-bs-target="#${id}" 
                     style="cursor:pointer;">
                    ${label}
                    <span class="badge bg-secondary rounded-pill">${counts[countKey] || 0}/${total}</span>
                </div>
                <div id="${id}" class="collapse mt-2">
                    <small class="text-muted">
                        ${symbolList}
                    </small>
                </div>
            `;

            stockIndicatorsEl.appendChild(li);
        });

    }


    // Stocks List
    const stocksListEl = document.getElementById("stocks-list");
    
    if (stocksListEl) {
        const assets = data.symbols;
        const searchEl = document.getElementById("stocks-search");

        // Function to render the list
        function renderAssets(data) {
            if (!data) return;
            stocksListEl.innerHTML = '';
            const list = data.slice(0, 10);

            list.forEach(asset => {
                const item = document.createElement("li");
                item.className = "list-group-item d-flex align-items-center gap-2";
                item.setAttribute("data-symbol", asset.symbol);
                item.style.cursor = "pointer";
                item.style.userSelect = "none";

                item.innerHTML = `
                    <div>
                        <img src="/static/images/${asset.symbol.split("/")[0].toLowerCase()}.png" width="20" height="20">
                    </div>
                    <div>${asset.name} (${asset.symbol})</div>
                    <div class="ms-auto">
                        <span>${asset.price.toFixed(2)}</span>
                    </div>
                `;

                item.addEventListener("click", () => loadAssetDetails("stocks", asset.symbol));
                stocksListEl.appendChild(item);
            });
        }

        // Initial render
        renderAssets(assets);

        // Search filter (case-insensitive, partial match)
        if (searchEl) {
            searchEl.addEventListener("input", () => {
                const query = searchEl.value.trim().toLowerCase();
                const filtered = assets.filter(asset =>
                    asset.symbol.toLowerCase().includes(query) ||
                    asset.name.toLowerCase().includes(query)
                );
                renderAssets(filtered);
            });
        }
    }
}

function updateCryptoDashboard(data) {
    // Market Status
    setTextContent(document.getElementById("crypto-market-status-value"), data.market_status);
    const marketBreadthEl = document.getElementById("crypto-market-breadth");
    updateChangeElement(marketBreadthEl, data.breadth_pct, 50, 1);

    // Volatility Index
    setTextContent(document.getElementById("crypto-volatility-status"), data.volatility_index?.toFixed(2));
    
    updateChangeElement(
        document.getElementById("crypto-volatility-value"), data.volatility_index, 0, 100);

    // Market Liquidity
    setTextContent(document.getElementById("crypto-liquidity-status"), data.market_liquidity.liquidity_status);
    setTextContent(document.getElementById("crypto-liquidity-score"), data.market_liquidity.liquidity_score);

    // Market Intelligence - Narrative
    setTextContent(document.getElementById("crypto-narrative-headline"), data.narrative.headline);
    setTextContent(document.getElementById("crypto-narrative-desc"), data.narrative.narrative);
    setTextContent(document.getElementById("crypto-narrative-timestamp"), data.narrative.generated_at);

    // Session 
    setTextContent(document.getElementById("crypto-current-session"), data.current_session);
    // Tech indicators
    setTextContent(document.getElementById("crypto-rsi-value"), data.technical_breadth.rsi_over_65);
    setTextContent(document.getElementById("macd-bullish-value"), data.technical_breadth.macd_bull_cross);
    // News
    const newsListEl = document.getElementById("crypto-news");
    if (data.news && newsListEl) {
          const topNews = data.news.slice(0, 3); // first 3

          // clear old news
          newsListEl.innerHTML = "";

          topNews.forEach(item => {
            const col = document.createElement("div");
            col.className = "col-md-6 col-lg-4";

            col.innerHTML = `
              <div class="card border-0 shadow-none mb-3">
                <div class="card-body">
                  <h6 class="card-title">
                    <a href="${item.url || '#'}" target="_blank" class="text-decoration-none">
                      ${item.title}
                    </a>
                  </h6>
                  <p class="card-text small text-muted">
                    ${item.description || "Visit website to view full item."}
                  </p>
                  <div class="d-flex justify-content-between align-items-center">
                    <small>${new Date(item.publishedAt).toLocaleString()}</small>
                  </div>
                </div>
              </div>
            `;

            newsListEl.appendChild(col);
          });
    }

    // Tech Indicators Accordion
    // Tech Indicators Accordion
    const cryptoIndicatorsEl = document.getElementById("crypto-tech-indicators");
    if (cryptoIndicatorsEl) {
        cryptoIndicatorsEl.innerHTML = "";

        const { counts, symbols } = data.technical_breadth;
        const total = counts.symbols_evaluated || 0;

        const indicatorsMap = [
            { label: "RSI Above 65", countKey: "rsi_over_65", symbolKey: "rsi_over" },
            { label: "MACD Bullish Cross", countKey: "macd_bull_cross", symbolKey: "macd_bull_cross" },
            { label: "Above 20-Day MA", countKey: "above_ma20", symbolKey: "above_ma20" },
            { label: "Above 50-Day MA", countKey: "above_ma50", symbolKey: "above_ma50" },
            { label: "Above 200-Day MA", countKey: "above_ma200", symbolKey: "above_ma200" },
            { label: "Above VWAP", countKey: "above_vwap", symbolKey: "above_vwap" },
            { label: "High Volume", countKey: "high_volume", symbolKey: "high_volume" }
        ];

        indicatorsMap.forEach(({ label, countKey, symbolKey }, idx) => {
            const id = `symbols-${countKey}-${idx}`;

            const li = document.createElement("li");
            li.className = "list-group-item px-0";

            const symbolList = (symbols[symbolKey] && symbols[symbolKey].length > 0)
                ? `<ul class="mb-0 ps-3">${symbols[symbolKey].map(s => `<li>${s}</li>`).join("")}</ul>`
                : "<em class='text-muted'>None</em>";

            li.innerHTML = `
                <div class="d-flex justify-content-between align-items-center" 
                     data-bs-toggle="collapse" 
                     data-bs-target="#${id}" 
                     style="cursor:pointer;">
                    ${label}
                    <span class="badge bg-secondary rounded-pill">${counts[countKey] || 0}/${total}</span>
                </div>
                <div id="${id}" class="collapse mt-2">
                    <small class="text-muted">
                        ${symbolList}
                    </small>
                </div>
            `;

            cryptoIndicatorsEl.appendChild(li);
        });

    }


    // Crypto Correlation Matrix
    cryptoCorrelationEl = document.getElementById("crypto-correlation-matrix");
    if (cryptoCorrelationEl) renderCorrelationMatrix(cryptoCorrelationEl, data.correlation_matrix);

    // Breadth Chart
    cryptoBreadthTrendEl = document.getElementById("crypto-breadth-trend");
    if (cryptoBreadthTrendEl) renderBreadthChart(cryptoBreadthTrendEl, data.breadth_series);

    dominanceEl = document.getElementById("dominance-analysis");
    if (dominanceEl) renderDominanceAnalysis(dominanceEl, data.narrative.dominance_analysis);

    // Volume Chart
    VolumeChartEl = document.getElementById("crypto-vol-chart");
    if (VolumeChartEl) renderVolumeChart(VolumeChartEl, data.market_liquidity.volume_ratio_avg, data.generated_at);

    // Market Makers
    const gainersEl = document.getElementById("crypto-top-gainers");
    const losersEl = document.getElementById("crypto-top-losers");
    if (gainersEl) {
        const { gainers, losers } = data.top_movers;

        /// Helper to generate list items
        function createListItem(item, isGainer = true) {
            return `
                <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                <span>${item.symbol}</span>
                <span>${item.latest.toFixed(2)}</span>
                <span class="badge ${isGainer ? 'bg-success' : 'bg-danger'}">
                    ${item.change_pct >= 0 ? '+' : ''}${item.change_pct.toFixed(2)}%
                </span>
                </li>
            `;
        }

        // Update lists
        gainersEl.innerHTML = gainers.map(item => createListItem(item, true)).join("");
        losersEl.innerHTML = losers.map(item => createListItem(item, false)).join("");
    }

    // Tech Indicators

    // Assets List
    const assetsListEl = document.getElementById("crypto-assets-list");
    
    if (assetsListEl) {
        const assets = data.symbols;
        const searchEl = document.getElementById("crypto-search");

        // Function to render the list
        function renderAssets(data) {
            if (!data) return;
            assetsListEl.innerHTML = '';
            const list = data.slice(0, 10);

            list.forEach(asset => {
                const item = document.createElement("li");
                item.className = "list-group-item d-flex align-items-center gap-2";
                item.setAttribute("data-symbol", asset.symbol);
                item.style.cursor = "pointer";
                item.style.userSelect = "none";

                item.innerHTML = `
                    <div>
                        <img src="/static/images/${asset.symbol.split("/")[0].toLowerCase()}.png" width="20" height="20">
                    </div>
                    <div>${asset.name} (${asset.symbol})</div>
                    <div class="ms-auto">
                        <span>${asset.price.toFixed(2)}</span>
                    </div>
                `;

                item.addEventListener("click", () => loadAssetDetails("crypto", asset.symbol));
                assetsListEl.appendChild(item);
            });
        }

        // Initial render
        renderAssets(assets);

        // Search filter (case-insensitive, partial match)
        if (searchEl) {
            searchEl.addEventListener("input", () => {
                const query = searchEl.value.trim().toLowerCase();
                const filtered = assets.filter(asset =>
                    asset.symbol.toLowerCase().includes(query) ||
                    asset.name.toLowerCase().includes(query)
                );
                renderAssets(filtered);
            });
        }
    }

}






// WebSocket connection management
document.addEventListener("DOMContentLoaded", () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const RECONNECT_DELAY = 5000;
    const MAX_RECONNECT_DELAY = 60000;

    let miSocket = null;
    const reconnectState = {
        attempts: 0,
        timeout: null,
    };

    const exponentialBackoff = (attempts) => {
        const base = Math.min(RECONNECT_DELAY * 2 ** attempts, MAX_RECONNECT_DELAY);
        const jitter = Math.random() * 1000; // up to +1s jitter to avoid sync storms
        return base + jitter;
    };

    const connectMiSocket = () => {
        // Clear previous reconnect timers
        clearTimeout(reconnectState.timeout);

        const wsUrl = `${wsProtocol}://${location.host}/ws/market-intelligence/`;
        miSocket = new WebSocket(wsUrl);

        miSocket.onopen = () => {
            console.log("[MI] Connected");
            reconnectState.attempts = 0;
        };

        miSocket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);

                // Handle system messages
                if (payload.type === "connection_established") {
                    console.log("[MI] Server:", payload.message);
                    return;
                }

                // Handle market intelligence (live + cached)
                if (payload.type === "market_intelligence" || payload.type === "cached_market_data") {
                    const msgdata = payload.payload;
                    console.log("payload: ", msgdata);

                    if (msgdata.asset_class === "forex") updateForexDashboard(msgdata);
                    if (msgdata.asset_class === "stocks") updateStocksDashboard(msgdata);
                    if (msgdata.asset_class === "crypto") updateCryptoDashboard(msgdata);
                }

            } catch (err) {
                console.error("[MI] Error parsing message:", err, event.data);
            }
        };

        miSocket.onclose = () => {
            reconnectState.attempts++;
            const delay = exponentialBackoff(reconnectState.attempts);
            console.warn(
                `[MI] Connection closed. Reconnecting in ${(delay / 1000).toFixed(1)}s (attempt ${reconnectState.attempts})`
            );
            reconnectState.timeout = setTimeout(connectMiSocket, delay);
        };

        miSocket.onerror = (error) => {
            console.error("[MI] WebSocket error:", error);
            // onclose will handle reconnection
        };
    };

    const initialize = () => {
        connectMiSocket();

        window.addEventListener("beforeunload", () => {
            if (miSocket && miSocket.readyState === WebSocket.OPEN) {
                miSocket.close(1000, "Page unloading");
            }
            clearTimeout(reconnectState.timeout);
        });
    };

    initialize();
});







