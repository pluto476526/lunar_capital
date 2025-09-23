



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


