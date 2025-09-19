// copilot/sockets/dash_socket.js

const SECTORMAP = {
  "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology", "GOOGL": "Technology", "META": "Technology",
  "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary", "DIS": "Consumer Discretionary", "NKE": "Consumer Discretionary",
  "JPM": "Financials", "BAC": "Financials", "GS": "Financials", "MS": "Financials", "V": "Financials", "MA": "Financials",
  "JNJ": "Healthcare", "PFE": "Healthcare", "UNH": "Healthcare", "MRK": "Healthcare", "ABT": "Healthcare", "TMO": "Healthcare",
  "PG": "Consumer Staples", "KO": "Consumer Staples", "PEP": "Consumer Staples", "WMT": "Consumer Staples", "COST": "Consumer Staples",
  "XOM": "Energy", "CVX": "Energy",
  "BA": "Industrials", "CAT": "Industrials", "UNP": "Industrials",
  "LIN": "Materials", "SHW": "Materials",
  "NEE": "Utilities", "DUK": "Utilities",
  "PLD": "Real Estate", "AMT": "Real Estate",
  "^GSPC": "Index", "^DJI": "Index", "^IXIC": "Index", "^RUT": "Index", "^FTSE": "Index"
};


// Theme configuration
const chartTheme = {
  light: {
    background: '#FFFFFF',
    text: {
      primary: '#333333',
      secondary: '#666666'
    },
    grid: '#EAEAEA',
    positive: '#26A69A',
    negative: '#EF5350',
    purple: {
      primary: '#8932FF',
      light: '#B894FF',
      lighter: '#E6D7FF'
    }
  },
  dark: {
    background: '#1A1D29',
    text: {
      primary: '#F0F0F0',
      secondary: '#AAAAAA'
    },
    grid: '#2A2F3D',
    positive: '#4CD8C8',
    negative: '#FF6B6B',
    purple: {
      primary: '#A45BFF',
      light: '#7B40CC',
      lighter: '#3A2A5C'
    }
  }
};

// Helper function to detect dark mode preference
function isDarkMode() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Get appropriate theme colors
function getThemeColors() {
  // return isDarkMode() ? chartTheme.dark : chartTheme.light;
    return chartTheme.light;
}

// Common chart configuration
const commonChartConfig = {
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif',
  toolbar: {
    show: true,
    tools: {
      download: true,
      selection: false,
      zoom: true,
      zoomin: true,
      zoomout: true,
      pan: false,
      reset: true
    }
  }
};

function renderIndexPerformanceChart(element, indexReturns) {
    const colors = getThemeColors();
    
    // Convert object → array of { symbol, daily }
    const entries = Object.entries(indexReturns).map(([symbol, values]) => ({
        symbol,
        daily: values.daily
    }));

    // Sort by daily return (descending)
    entries.sort((a, b) => b.daily - a.daily);

    // Extract categories + daily arrays
    const categories = entries.map(e => e.symbol);
    const daily = entries.map(e => e.daily);

    const options = {
        chart: {
            type: 'bar',
            height: 400,
            background: colors.background,
            toolbar: { 
                show: true,
                tools: {
                    ...commonChartConfig.toolbar.tools
                }
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        plotOptions: {
            bar: {
                horizontal: true,
                barHeight: '40%',
                borderRadius: 8,
                dataLabels: { 
                    position: 'right',
                    orientation: 'horizontal'
                }
            }
        },
        colors: daily.map(val => val >= 0 ? colors.positive : colors.negative),
        dataLabels: {
            enabled: true,
            style: { 
                fontSize: '12px', 
                fontWeight: 500,
                colors: [colors.background]
            },
            formatter: (val) => val.toFixed(2) + '%',
            background: {
                enabled: true,
                foreColor: colors.text.primary,
                borderRadius: 4,
                padding: 4,
                opacity: 0.8,
                borderWidth: 0
            }
        },
        series: [{
            name: 'Daily Return',
            data: daily
        }],
        xaxis: {
            categories: categories,
            title: {
                text: 'Return (%)',
                style: { 
                    fontSize: '14px', 
                    fontWeight: 600,
                    color: colors.text.primary
                }
            },
            labels: {
                style: {
                    colors: colors.text.secondary
                },
                formatter: (val) => val.toFixed(1) + '%'
            },
            axisBorder: {
                show: true,
                color: colors.grid
            },
            axisTicks: {
                show: true,
                color: colors.grid
            }
        },
        yaxis: {
            labels: { 
                style: { 
                    fontSize: '14px', 
                    fontWeight: 500,
                    colors: colors.text.primary
                }
            }
        },
        tooltip: {
            theme: isDarkMode() ? 'dark' : 'light',
            style: {
                fontSize: '14px'
            },
            y: { 
                formatter: (val) => val.toFixed(2) + "%",
                title: {
                    formatter: () => 'Return: '
                }
            }
        },
        grid: {
            borderColor: colors.grid,
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        title: {
            text: 'Global Index Daily Returns',
            align: 'center',
            style: { 
                fontSize: '18px', 
                fontWeight: 'bold',
                color: colors.text.primary
            }
        },
        subtitle: {
            text: 'Sorted by performance',
            align: 'center',
            style: {
                color: colors.text.secondary
            }
        }
    };

    // Clear previous chart if it exists
    if (element.performanceBarChart) {
        element.performanceBarChart.updateOptions(options);
        element.performanceBarChart.updateSeries([{ data: daily }]);
    } else {
        // Create and store new chart
        element.performanceBarChart = new ApexCharts(element, options);
        element.performanceBarChart.render();
    }
}

function renderSectorPerformanceTreemap(element, sectorData) {
    const colors = getThemeColors();
    
    // Convert object -> array
    const sectors = Object.entries(sectorData).map(([sector, value]) => ({
        x: sector.charAt(0).toUpperCase() + sector.slice(1),
        y: parseFloat(value.toFixed(2))
    }));

    const options = {
        chart: {
            type: "treemap",
            height: 400,
            width: "100%",
            background: colors.background,
            toolbar: { 
                show: true,
                tools: {
                    ...commonChartConfig.toolbar.tools
                }
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        series: [{ data: sectors }],
        legend: { 
            show: true,
            position: 'bottom',
            labels: {
                colors: colors.text.primary
            }
        },
        plotOptions: {
            treemap: {
                distributed: true,
                enableShades: true,
                shadeIntensity: 0.2,
                reverseNegativeShade: true,
                colorScale: {
                    ranges: [
                        { from: -100, to: -5, color: colors.negative, name: "Strong Negative" },
                        { from: -5, to: 0, color: colors.purple.light, name: "Slight Negative" },
                        { from: 0.0001, to: 5, color: colors.purple.lighter, name: "Slight Positive" },
                        { from: 5, to: 100, color: colors.positive, name: "Strong Positive" }
                    ]
                }

            }
        },
        dataLabels: {
            enabled: true,
            style: { 
                fontSize: "14px", 
                fontWeight: "bold", 
                colors: [colors.background]
            },
            formatter: function (text, opts) {
                const value = opts.value;
                return `${text}\n${value.toFixed(2)}%`;
            },
            background: {
                enabled: true,
                foreColor: colors.text.primary,
                borderRadius: 4,
                padding: 4,
                opacity: 0.8,
                borderWidth: 0
            }
        },
        tooltip: {
            theme: isDarkMode() ? 'dark' : 'light',
            style: {
                fontSize: '14px'
            },
            y: { 
                formatter: val => `${val.toFixed(2)}%`,
                title: {
                    formatter: () => 'Return: '
                }
            }
        },
        title: {
            text: 'Sector Performance Treemap',
            align: 'center',
            style: {
                color: colors.text.primary,
                fontSize: '18px',
                fontWeight: 'bold'
            }
        },
        subtitle: {
            text: 'Size represents performance magnitude',
            align: 'center',
            style: {
                color: colors.text.secondary
            }
        }
    };

    if (element.performanceTreemap) {
         element.performanceTreemap.updateSeries([{ data: sectors }])
    } else {
    
        // Create and store new chart
        element.performanceTreemap = new ApexCharts(element, options);
        element.performanceTreemap.render();
    }
}

function renderTechnicalBreadth(data) {
    const { macd_bull_cross, rsi_over_70, symbols_evaluated } = data;
    const colors = getThemeColors();

    // Utility to build a donut
    function buildDonut(elementId, value, total, label, color) {
        const percentage = total > 0 ? (value / total) * 100 : 0;

        const options = {
            chart: {
                type: 'radialBar',
                height: 280,
                background: colors.background,
                sparkline: { enabled: false },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800
                }
            },
            theme: {
                mode: isDarkMode() ? 'dark' : 'light'
            },
            series: [percentage],
            colors: [color],
            plotOptions: {
                radialBar: {
                    hollow: { 
                        size: '60%',
                        background: colors.background
                    },
                    track: { 
                        background: colors.grid,
                        strokeWidth: '100%'
                    },
                    dataLabels: {
                        name: {
                            show: true,
                            offsetY: 20,
                            fontSize: '14px',
                            fontWeight: 600,
                            color: colors.text.primary,
                            formatter: () => label
                        },
                        value: {
                            show: true,
                            fontSize: '24px',
                            fontWeight: 700,
                            color: colors.text.primary,
                            formatter: (val) => val.toFixed(1) + '%'
                        }
                    }
                }
            },
            labels: [label],
            tooltip: {
                enabled: true,
                theme: isDarkMode() ? 'dark' : 'light',
                style: {
                    fontSize: '14px'
                },
                y: {
                    formatter: () => `${value}/${total} (${percentage.toFixed(1)}%)`
                }
            },
            stroke: {
                lineCap: 'round'
            }
        };

        const element = document.querySelector(elementId);
        // if (element && element._chart) element._chart.destroy(); // clear previous
        // element._chart = new ApexCharts(element, options);
        // element._chart.render();

        if (element) {
            if (element.donutCharts) {
                element.donutCharts.updateSeries(series);
            } else {
                element.donutCharts = new ApexCharts(element, options);
                element.donutCharts.render();
            }
        }

    }

    // Render both donuts
    buildDonut("#macd-donut", macd_bull_cross, symbols_evaluated, "MACD Bull Cross", colors.purple.primary);
    buildDonut("#rsi-donut", rsi_over_70, symbols_evaluated, "RSI > 70", colors.purple.light);
}

function renderStockCorrelationMatrix(element, sectorCorrelationMatrix) {
    const sectors = Object.keys(sectorCorrelationMatrix);

    const series = sectors.map(rowSector => ({
        name: rowSector,
        data: sectors.map(colSector => ({
          x: colSector,
          y: sectorCorrelationMatrix[rowSector][colSector]
        }))
    }));

    const options = {
        chart: { type: 'heatmap', height: 700 },
        plotOptions: {
          heatmap: {
            colorScale: {
              ranges: [
                { from: -1, to: -0.5, color: '#e53935', name: 'Negative' },
                { from: -0.5, to: 0.5, color: '#eeeeee', name: 'Neutral' },
                { from: 0.5, to: 1, color: '#2e7d32', name: 'Positive' }
              ]
            }
          }
        },
        dataLabels: { enabled: false },
        xaxis: { categories: sectors },
        title: { text: 'Sector Correlation Matrix' },
        series: series
    };

    // If chart already exists → update
    if (element.stockCorrChart) {
        element.stockCorrChart.updateSeries(series);
    } else {
        element.stockCorrChart = new ApexCharts(element, options);
        element.stockCorrChart.render();
    }

    //const chart = new ApexCharts(element, options);
    //chart.render();
}

function renderCorrelationMatrix(element, correlationMatrix) {
    const colors = getThemeColors();
    const tickers = Object.keys(correlationMatrix);

    // Convert nested object → Apex heatmap format
    const series = tickers.map(rowTicker => {
        return {
            name: rowTicker,
            data: tickers.map(colTicker => {
                return {
                    x: colTicker,
                    y: correlationMatrix[rowTicker][colTicker]
                };
            })
        };
    });

    const options = {
        chart: {
            type: 'heatmap',
            height: 500,
            background: colors.background,
            toolbar: { 
                show: true,
                tools: {
                    ...commonChartConfig.toolbar.tools
                }
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        dataLabels: {
            enabled: true,
            style: {
                fontSize: '11px',
                colors: [colors.background]
            },
            formatter: (val) => val.toFixed(2)
        },
        plotOptions: {
            heatmap: {
                shadeIntensity: 0.6,
                radius: 4,
                useFillColorAsStroke: false,
                colorScale: {
                    inverse: false,
                    ranges: [
                        { from: -1, to: -0.75, color: colors.negative, name: 'Very Strong Negative' },
                        { from: -0.75, to: -0.5, color: colors.purple.light, name: 'Strong Negative' },
                        { from: -0.5, to: -0.25, color: colors.purple.lighter, name: 'Moderate Negative' },
                        { from: -0.25, to: 0, color: colors.grid, name: 'Weak Negative' },
                        { from: 0, to: 0.25, color: colors.grid, name: 'Weak Positive' },
                        { from: 0.25, to: 0.5, color: colors.purple.lighter, name: 'Moderate Positive' },
                        { from: 0.5, to: 0.75, color: colors.purple.light, name: 'Strong Positive' },
                        { from: 0.75, to: 1, color: colors.positive, name: 'Very Strong Positive' }
                    ]
                }
            }
        },
        xaxis: {
            categories: tickers,
            labels: { 
                rotate: -45, 
                style: { 
                    fontSize: '11px',
                    colors: colors.text.primary
                },
                trim: true
            },
            axisBorder: {
                show: true,
                color: colors.grid
            },
            axisTicks: {
                show: true,
                color: colors.grid
            },
            title: {
                text: 'Tickers',
                style: {
                    color: colors.text.primary
                }
            }
        },
        yaxis: {
            labels: { 
                style: { 
                    fontSize: '11px',
                    colors: colors.text.primary
                }
            },
            title: {
                text: 'Tickers',
                style: {
                    color: colors.text.primary
                }
            }
        },
        tooltip: {
            theme: isDarkMode() ? 'dark' : 'light',
            style: {
                fontSize: '14px'
            },
            y: {
                formatter: (val) => val.toFixed(2),
                title: {
                    formatter: () => 'Correlation: '
                }
            }
        },
        legend: {
            show: true,
            position: 'bottom',
            fontSize: '12px',
            markers: { 
                radius: 6,
                width: 12,
                height: 12
            },
            labels: {
                colors: colors.text.primary
            }
        },
        title: {
            text: 'FX Correlation Matrix',
            align: 'center',
            style: { 
                fontSize: '18px', 
                fontWeight: 'bold',
                color: colors.text.primary
            }
        },
        grid: {
            borderColor: colors.grid,
            strokeDashArray: 4
        },
        series: series
    };

    // If chart already exists → update
    if (element.correlationChart) {
        element.correlationChart.updateOptions(options);
        element.correlationChart.updateSeries(series);
    } else {
        element.correlationChart = new ApexCharts(element, { ...options, series });
        element.correlationChart.render();
    }
}

function renderKeyLevelsLineChart(element, keyLevels) {
    const colors = getThemeColors();
    
    // Create series of current prices (scatter points)
    const series = [{
        name: "Current Price",
        type: "scatter",
        data: keyLevels.map(item => ({
            x: item.symbol,
            y: item.price
        }))
    }];

    const options = {
        chart: {
            type: "line",
            height: 400,
            background: colors.background,
            toolbar: { 
                show: true,
                tools: {
                    ...commonChartConfig.toolbar.tools
                }
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        series: series,
        markers: {
            size: 6,
            colors: [colors.purple.primary],
            strokeColors: colors.background,
            strokeWidth: 2
        },
        stroke: {
            width: 0 // No line for scatter
        },
        xaxis: {
            categories: keyLevels.map(e => e.symbol),
            title: { 
                text: "FX Pairs",
                style: {
                    color: colors.text.primary
                }
            },
            labels: {
                style: {
                    colors: colors.text.primary
                }
            },
            axisBorder: {
                show: true,
                color: colors.grid
            },
            axisTicks: {
                show: true,
                color: colors.grid
            }
        },
        yaxis: {
            title: { 
                text: "Price",
                style: {
                    color: colors.text.primary
                }
            },
            labels: {
                style: {
                    colors: colors.text.primary
                }
            }
        },
        tooltip: {
            theme: isDarkMode() ? 'dark' : 'light',
            style: {
                fontSize: '14px'
            },
            y: {
                formatter: (val, opts) => {
                    const entry = keyLevels[opts.dataPointIndex];
                    return `Price: ${val}, Key Level: ${entry.key_level} (${entry.type}, dist ${entry.distance_pct.toFixed(2)}%)`;
                }
            }
        },
        annotations: {
            yaxis: keyLevels.map(item => ({
                y: item.key_level,
                borderColor: item.type === "support" ? colors.positive : colors.negative,
                label: {
                    text: `${item.symbol} ${item.type} @ ${item.key_level}`,
                    style: {
                        color: colors.background,
                        background: item.type === "support" ? colors.positive : colors.negative,
                        fontSize: '12px',
                        padding: {
                            left: 10,
                            right: 10,
                            top: 4,
                            bottom: 4
                        }
                    }
                }
            }))
        },
        title: {
            text: "FX Key Levels (Support & Resistance)",
            align: "center",
            style: {
                color: colors.text.primary,
                fontSize: '18px',
                fontWeight: 'bold'
            }
        },
        grid: {
            borderColor: colors.grid,
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        }
    };

    if (element.keyLevelsChart) {
        element.keyLevelsChart.updateOptions(options);
        element.keyLevelsChart.updateSeries(series);
    } else {
        element.keyLevelsChart = new ApexCharts(element, options);
        element.keyLevelsChart.render();
    }
}

function renderBreadthChart(element, breadthSeries) {
    const colors = getThemeColors();
    const series = [{
        name: "Breadth %",
        type: "line",
        data: breadthSeries.map((v, i) => ({ x: i + 1, y: v }))
    }];

    const options = {
        chart: {
            type: "line",
            height: 400,
            background: colors.background,
            toolbar: { 
                show: true,
                tools: {
                    ...commonChartConfig.toolbar.tools
                }
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        series: series,
        stroke: { 
            curve: "smooth", 
            width: 3,
            colors: [colors.purple.primary]
        },
        markers: {
            size: 5,
            colors: breadthSeries.map(v => v >= 50 ? colors.positive : colors.negative),
            strokeColors: colors.background,
            strokeWidth: 2
        },
        xaxis: {
            title: { 
                text: "Previous Calculations",
                style: {
                    color: colors.text.primary
                }
            },
            labels: {
                style: {
                    colors: colors.text.primary
                }
            },
            axisBorder: {
                show: true,
                color: colors.grid
            },
            axisTicks: {
                show: true,
                color: colors.grid
            }
        },
        yaxis: {
            min: 0,
            max: 100,
            title: { 
                text: "Breadth %",
                style: {
                    color: colors.text.primary
                }
            },
            labels: {
                style: {
                    colors: colors.text.primary
                },
                formatter: val => `${val}%`
            }
        },
        tooltip: {
            theme: isDarkMode() ? 'dark' : 'light',
            style: {
                fontSize: '14px'
            },
            y: {
                formatter: (val) => `${val.toFixed(1)}%`
            }
        },
        annotations: {
            yaxis: [
                {
                    y: 50,
                    borderColor: colors.text.secondary,
                    strokeDashArray: 4,
                    label: {
                        text: "Bullish Threshold (50)",
                        style: {
                            color: colors.background,
                            background: colors.text.secondary,
                            fontSize: '12px',
                            padding: {
                                left: 10,
                                right: 10,
                                top: 4,
                                bottom: 4
                            }
                        }
                    }
                },
                {
                    y: 50,
                    y2: 100,
                    fillColor: isDarkMode() ? "rgba(76, 216, 200, 0.1)" : "rgba(38, 166, 154, 0.1)",
                    opacity: 0.2,
                    label: {
                        text: "Bullish Zone",
                        style: {
                            color: colors.positive,
                            background: isDarkMode() ? "rgba(76, 216, 200, 0.3)" : "rgba(38, 166, 154, 0.3)",
                            fontSize: '12px'
                        }
                    }
                },
                {
                    y: 0,
                    y2: 50,
                    fillColor: isDarkMode() ? "rgba(255, 107, 107, 0.1)" : "rgba(239, 83, 80, 0.1)",
                    opacity: 0.2,
                    label: {
                        text: "Bearish Zone",
                        style: {
                            color: colors.negative,
                            background: isDarkMode() ? "rgba(255, 107, 107, 0.3)" : "rgba(239, 83, 80, 0.3)",
                            fontSize: '12px'
                        }
                    }
                }
            ]
        },
        title: {
            text: "Crypto Market Breadth",
            align: "center",
            style: {
                color: colors.text.primary,
                fontSize: '18px',
                fontWeight: 'bold'
            }
        },
        grid: {
            borderColor: colors.grid,
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        }
    };

    if (element.breadthChart) {
        element.breadthChart.updateOptions(options, true, true);
        element.breadthChart.updateSeries(series);
    } else {
        element.breadthChart = new ApexCharts(element, options);
        element.breadthChart.render();
    }
}

function renderDominanceAnalysis(element, dominanceData) {
    const colors = getThemeColors();
    
    // Clear the element first
    element.innerHTML = "";

    // Outer container
    const container = document.createElement("div");
    container.className = "dominance-container";
    container.style.display = "flex";
    container.style.flexDirection = "column";  // vertical stack
    container.style.gap = "20px";
    container.style.padding = "20px";
    container.style.background = colors.background;
    container.style.borderRadius = "12px";

    // --- Row 1: BTC price + dominance dial ---
    const topRow = document.createElement("div");
    topRow.style.display = "flex";
    topRow.style.flexDirection = "row";
    topRow.style.gap = "20px";

    // BTC Price Card
    const btcPriceEl = document.createElement("div");
    btcPriceEl.className = "btc-price-card";
    btcPriceEl.style.flex = "1";
    btcPriceEl.style.padding = "15px";
    btcPriceEl.style.background = isDarkMode() ? "#2A2F3D" : "#F5F5F5";
    btcPriceEl.style.borderRadius = "8px";
    btcPriceEl.style.textAlign = "center";

    const btcChangePct = (dominanceData.btc_change * 100).toFixed(2);

    btcPriceEl.innerHTML = `
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;">
            <h4 style="margin: 0 0 6px 0; font-size: 1.4rem; color: ${colors.text.primary};">
                BTC $${dominanceData.btc_price.toLocaleString()}
            </h4>
            <span style="font-size: 1rem; color: ${btcChangePct >= 0 ? colors.positive : colors.negative}; font-weight: 500;">
                ${btcChangePct >= 0 ? "+" : ""}${btcChangePct}%
            </span>
        </div>
    `;



    // BTC Dominance Radial
    const dominanceEl = document.createElement("div");
    dominanceEl.className = "dominance-chart";
    dominanceEl.style.flex = "1";
    dominanceEl.style.display = "flex";
    dominanceEl.style.justifyContent = "center";
    dominanceEl.style.alignItems = "center";

    // Add both to top row
    topRow.appendChild(btcPriceEl);
    topRow.appendChild(dominanceEl);

    // --- Row 2: Altcoin Performance Bars ---
    const altEl = document.createElement("div");
    altEl.className = "altcoin-chart";
    altEl.style.width = "100%";

    // Add everything to container
    container.appendChild(topRow);
    container.appendChild(altEl);

    // Finally append to DOM
    element.appendChild(container);

    
    // Now render charts after elements are in DOM
    // Calculate responsive dimensions
    const containerWidth = container.clientWidth;
    
    // BTC Dominance Chart
    const dominanceOptions = {
        chart: {
            type: "radialBar",
            height: Math.min(200, containerWidth * 0.6),
            width: "100%",
            background: "transparent"
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        series: [dominanceData.btc_dominance],
        labels: ["BTC Dominance"],
        colors: [colors.purple.primary],
        plotOptions: {
            radialBar: {
                hollow: { 
                    size: "60%",
                    background: "transparent"
                },
                track: {
                    background: colors.grid
                },
                dataLabels: {
                    name: { 
                        show: true, 
                        fontSize: "16px",
                        color: colors.text.primary,
                        fontWeight: 500
                    },
                    value: {
                        formatter: v => `${v}%`,
                        fontSize: "24px",
                        fontWeight: "bold",
                        color: colors.text.primary
                    }
                }
            }
        },
    };
    const dominanceChart = new ApexCharts(dominanceEl, dominanceOptions);
    dominanceChart.render();
    
    // Altcoin Performance Chart
    const altPerf = Object.entries(dominanceData.altcoin_performance).map(([coin, perf]) => ({
        x: coin,
        y: (perf * 100).toFixed(2)
    }));

    const altOptions = {
        chart: { 
            type: "bar", 
            height: Math.min(300, containerWidth * 0.8),
            width: "100%",
            background: "transparent"
        },
        theme: {
            mode: isDarkMode() ? 'dark' : 'light'
        },
        series: [{ name: "Alt Performance (%)", data: altPerf }],
        plotOptions: {
            bar: {
                horizontal: true,
                barHeight: '40%',
                borderRadius: 4,
                colors: {
                    ranges: [
                        { from: -100, to: 0, color: colors.negative },
                        { from: 0, to: 100, color: colors.positive }
                    ]
                }
            }
        },
        dataLabels: { 
            enabled: true, 
            formatter: val => `${val}%`,
            style: {
                colors: [colors.background]
            }
        },
        xaxis: {
            title: { 
                text: "Performance (%)",
                style: {
                    color: colors.text.primary
                }
            },
            labels: {
                style: {
                    colors: colors.text.primary
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: colors.text.primary
                }
            }
        },
        grid: {
            borderColor: colors.grid,
            strokeDashArray: 4
        },
        title: {
            text: "Altcoin Performance",
            align: "center",
            style: {
                color: colors.text.primary,
                fontSize: '16px',
                fontWeight: 'bold'
            }
        }
    };
    const altChart = new ApexCharts(altEl, altOptions);
    altChart.render();

    // Save chart refs for potential updates
    element.dominanceChart = dominanceChart;
    element.altChart = altChart;
}



function renderVolumeChart(element, volumeAvg, timestamp) {
    const volumeHistory = [];
    const MAX_POINTS = 100;

    // Save incoming volume data point
    volumeHistory.push({
        x: new Date(timestamp),
        y: volumeAvg
    });

    if (volumeHistory.length > MAX_POINTS) {
        volumeHistory.shift(); // keep memory small
    }

    // Create series with just the volume ratio data
    const series = [{
        name: "Volume Ratio",
        data: [...volumeHistory]
    }];

    const options = {
        chart: {
            type: "line",
            toolbar: { show: false },
            animations: { enabled: true },
            background: "#1e293b",
            foreColor: "#e2e8f0"
        },
        stroke: {
            width: 2,
            curve: 'smooth'
        },
        colors: ["#0ea5e9"],
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
            min: 0,
            max: 2,
            tickAmount: 5,
            labels: {
                formatter: function(val) {
                    return val.toFixed(1);
                },
                style: {
                    colors: '#94a3b8'
                }
            },
            title: {
                text: "Volume Ratio",
                style: {
                    color: '#94a3b8'
                }
            }
        },
        tooltip: {
            shared: true,
            x: { format: "HH:mm" },
            theme: "dark",
            y: {
                formatter: function(val) {
                    return val.toFixed(2);
                }
            }
        },
        markers: {
            size: 3,
            strokeColors: '#0ea5e9',
            strokeWidth: 2,
            hover: {
                size: 5
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
        },
        annotations: {
            yaxis: [
                {
                    y: 1,
                    borderColor: '#22c55e',
                    label: {
                        text: "Neutral (1.0)",
                        style: {
                            background: '#22c55e',
                            color: "#fff",
                            fontSize: "12px"
                        }
                    }
                },
                {
                    y: 1.5,
                    borderColor: '#f59e0b',
                    label: {
                        text: "High (1.5)",
                        style: {
                            background: '#f59e0b',
                            color: "#fff",
                            fontSize: "12px"
                        }
                    }
                },
                {
                    y: 0.5,
                    borderColor: '#ef4444',
                    label: {
                        text: "Low (0.5)",
                        style: {
                            background: '#ef4444',
                            color: "#fff",
                            fontSize: "12px"
                        }
                    }
                }
            ]
        }
    };

    if (element.volumeChart) {
        element.volumeChart.updateOptions(options);
        element.volumeChart.updateSeries(series);
    } else {
        element.volumeChart = new ApexCharts(element, options);
        element.volumeChart.render();
    }
}

// Function to load asset details
function loadAssetDetails(symbol) {
    const detailsContainer = document.getElementById('crypto-asset-details');
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
            symbol: symbol
        }));
    } else {
        console.warn("Symbol socket not connected.");
    }
}

function renderAssetDetails(data) {
    const detailsContainer = document.getElementById('crypto-asset-details');
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

// Helper function for the button click
function viewFullAnalysis(symbol) {
    // Clean up symbol (e.g., BTC/USDT → BTCUSDT)
    const cleanSymbol = symbol.replace("/", "");

    // Build full URL dynamically
    const targetUrl = `${window.location.origin}/co-pilot/crypto/${cleanSymbol}`;

    // Redirect
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

    // Tech Indicators
    

    // Key Levels
    fxKeyLevelEl = document.getElementById("fx-key-levels");
    if (fxKeyLevelEl) renderKeyLevelsLineChart(fxKeyLevelEl, data.narrative.key_levels);
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

    // Market Conditions Summary
    if (data.technical_breadth) {
        renderTechnicalBreadth(data.technical_breadth);
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
        assetsListEl.innerHTML = '';
        // Merge gainers and losers into one array
        const movers = [...data.top_movers.gainers, ...data.top_movers.losers];

        movers.forEach(asset => {
            let changeClass = "text-muted";
            if (asset.change_pct > 0) changeClass = "text-success";
            else if (asset.change_pct < 0) changeClass = "text-danger";

            const item = document.createElement("li");
            item.className = "list-group-item d-flex align-items-center gap-2";
            item.setAttribute("data-symbol", asset.symbol);
            item.style.cursor = "pointer";
            item.style.userSelect = "none";


            item.innerHTML = `
                <div>
                    <img src="/static/images/${asset.symbol.split("/")[0].toLowerCase()}.png" width="20" height="20">
                </div>
                <div>${asset.symbol}</div>
                <div class="ms-auto">
                    <span class="${changeClass}">${asset.latest.toFixed(2)}</span>
                </div>
            `;

            item.addEventListener("click", () => loadAssetDetails(asset.symbol));
            assetsListEl.appendChild(item);
        });
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
                    console.log("[SERVER] Market data:", msgdata);

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







