// =============================
// Unified Chart Theme
// =============================
const chartTheme = {
  light: {
    background: "#FFFFFF",
    text: {
      primary: "#222222",
      secondary: "#555555",
    },
    grid: "#EAEAEA",
    palette: [
      "rgba(38, 166, 154, 0.9)", // teal
      "rgba(239, 83, 80, 0.9)",  // red
      "rgba(137, 50, 255, 0.9)", // purple
      "rgba(255, 193, 7, 0.9)",  // amber
      "rgba(33, 150, 243, 0.9)", // blue
    ],
    paletteFill: [
      "rgba(38, 166, 154, 0.25)",
      "rgba(239, 83, 80, 0.25)",
      "rgba(137, 50, 255, 0.25)",
      "rgba(255, 193, 7, 0.25)",
      "rgba(33, 150, 243, 0.25)",
    ],
  },
  dark: {
    background: "#1A1D29",
    text: {
      primary: "#F0F0F0",
      secondary: "#AAAAAA",
    },
    grid: "#2A2F3D",
    palette: [
      "rgba(76, 216, 200, 0.9)", 
      "rgba(255, 107, 107, 0.9)", 
      "rgba(164, 91, 255, 0.9)", 
      "rgba(255, 214, 102, 0.9)", 
      "rgba(100, 181, 246, 0.9)",
    ],
    paletteFill: [
      "rgba(76, 216, 200, 0.25)",
      "rgba(255, 107, 107, 0.25)",
      "rgba(164, 91, 255, 0.25)",
      "rgba(255, 214, 102, 0.25)",
      "rgba(100, 181, 246, 0.25)",
    ],
  },
};

// =============================
// Helpers
// =============================
function isDarkMode() {
  return (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

function getThemeColors() {
  return isDarkMode() ? chartTheme.dark : chartTheme.light;
}

// =============================
// Common Chart Config
// =============================
const commonChartConfig = {
  chart: {
    background: "transparent",
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
        reset: true,
      },
    },
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800
    }
  },
  stroke: {
    curve: "smooth",
    width: 2,
  },
  grid: {
    borderColor: getThemeColors().grid,
    strokeDashArray: 4,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
  },
  tooltip: {
    theme: isDarkMode() ? "dark" : "light",
    style: { fontSize: "14px" },
  },
  dataLabels: { 
    enabled: false,
    style: {
      fontSize: '12px',
      fontWeight: 500,
      colors: [getThemeColors().background]
    },
    background: {
      enabled: true,
      foreColor: getThemeColors().text.primary,
      borderRadius: 4,
      padding: 4,
      opacity: 0.8,
      borderWidth: 0
    }
  },
  legend: {
    labels: { colors: getThemeColors().text.primary },
    fontSize: "13px",
    fontWeight: 500,
    position: 'bottom'
  },
  xaxis: {
    labels: {
      style: {
        colors: getThemeColors().text.secondary,
        fontSize: "12px",
      },
    },
    axisBorder: {
      show: true,
      color: getThemeColors().grid
    },
    axisTicks: {
      show: true,
      color: getThemeColors().grid
    }
  },
  yaxis: {
    labels: {
      style: {
        colors: getThemeColors().text.secondary,
        fontSize: "12px",
      },
    },
  },
};

// =============================
// Chart Functions (Refactored)
// =============================

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
        ...commonChartConfig,
        chart: {
            ...commonChartConfig.chart,
            type: 'bar',
            height: 400,
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
        colors: daily.map(val => val >= 0 ? colors.palette[0] : colors.palette[1]),
        dataLabels: {
            ...commonChartConfig.dataLabels,
            enabled: true,
            formatter: (val) => val.toFixed(2) + '%',
        },
        series: [{
            name: 'Daily Return',
            data: daily
        }],
        xaxis: {
            ...commonChartConfig.xaxis,
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
                ...commonChartConfig.xaxis.labels,
                formatter: (val) => val.toFixed(1) + '%'
            },
        },
        yaxis: {
            ...commonChartConfig.yaxis,
            labels: { 
                style: { 
                    fontSize: '14px', 
                    fontWeight: 500,
                    colors: colors.text.primary
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

    if (element.performanceBarChart) {
        element.performanceBarChart.updateOptions(options);
        element.performanceBarChart.updateSeries([{ data: daily }]);
    } else {
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
        ...commonChartConfig,
        chart: {
            ...commonChartConfig.chart,
            type: "treemap",
            height: 400,
            width: "100%"
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
                        { from: -100, to: -5, color: colors.palette[1], name: "Strong Negative" },
                        { from: -5, to: 0, color: colors.palette[2], name: "Slight Negative" },
                        { from: 0.0001, to: 5, color: colors.paletteFill[2], name: "Slight Positive" },
                        { from: 5, to: 100, color: colors.palette[0], name: "Strong Positive" }
                    ]
                }
            }
        },
        dataLabels: {
            ...commonChartConfig.dataLabels,
            enabled: true,
            formatter: function (text, opts) {
                const value = opts.value;
                return `${text}\n${value.toFixed(2)}%`;
            },
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
        element.performanceTreemap = new ApexCharts(element, options);
        element.performanceTreemap.render();
    }
}

function renderTechnicalBreadth(data) {
    const { macd_bull_cross, rsi_over_70, symbols_evaluated } = data;
    const colors = getThemeColors();

    function buildDonut(elementId, value, total, label, color) {
        const percentage = total > 0 ? (value / total) * 100 : 0;

        const options = {
            ...commonChartConfig,
            chart: {
                ...commonChartConfig.chart,
                type: 'radialBar',
                height: 280,
                sparkline: { enabled: false }
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
            stroke: {
                lineCap: 'round'
            }
        };

        const element = document.querySelector(elementId);
        if (element) {
            if (element.donutCharts) {
                element.donutCharts.updateSeries([percentage]);
            } else {
                element.donutCharts = new ApexCharts(element, options);
                element.donutCharts.render();
            }
        }
    }

    buildDonut("#macd-donut", macd_bull_cross, symbols_evaluated, "MACD Bull Cross", colors.palette[2]);
    buildDonut("#rsi-donut", rsi_over_70, symbols_evaluated, "RSI > 70", colors.palette[3]);
}

function renderCorrelationMatrix(element, correlationMatrix) {
    const colors = getThemeColors();
    const tickers = Object.keys(correlationMatrix);

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
        ...commonChartConfig,
        chart: {
            ...commonChartConfig.chart,
            type: 'heatmap',
            height: 500
        },
        dataLabels: {
            ...commonChartConfig.dataLabels,
            enabled: true,
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
                        { from: -1, to: -0.75, color: colors.palette[1], name: 'Very Strong Negative' },
                        { from: -0.75, to: -0.5, color: colors.palette[2], name: 'Strong Negative' },
                        { from: -0.5, to: -0.25, color: colors.paletteFill[2], name: 'Moderate Negative' },
                        { from: -0.25, to: 0, color: colors.grid, name: 'Weak Negative' },
                        { from: 0, to: 0.25, color: colors.grid, name: 'Weak Positive' },
                        { from: 0.25, to: 0.5, color: colors.paletteFill[0], name: 'Moderate Positive' },
                        { from: 0.5, to: 0.75, color: colors.palette[2], name: 'Strong Positive' },
                        { from: 0.75, to: 1, color: colors.palette[0], name: 'Very Strong Positive' }
                    ]
                }
            }
        },
        xaxis: {
            ...commonChartConfig.xaxis,
            categories: tickers,
            labels: { 
                ...commonChartConfig.xaxis.labels,
                rotate: -45,
                trim: true
            },
            title: {
                text: 'Tickers',
                style: {
                    color: colors.text.primary
                }
            }
        },
        yaxis: {
            ...commonChartConfig.yaxis,
            title: {
                text: 'Tickers',
                style: {
                    color: colors.text.primary
                }
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
        series: series
    };

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
    
    const series = [{
        name: "Current Price",
        type: "scatter",
        data: keyLevels.map(item => ({
            x: item.symbol,
            y: item.price
        }))
    }];

    const options = {
        ...commonChartConfig,
        chart: {
            ...commonChartConfig.chart,
            type: "line",
            height: 400
        },
        series: series,
        markers: {
            size: 6,
            colors: [colors.palette[2]],
            strokeColors: colors.background,
            strokeWidth: 2
        },
        stroke: {
            width: 0
        },
        xaxis: {
            ...commonChartConfig.xaxis,
            categories: keyLevels.map(e => e.symbol),
            title: { 
                text: "FX Pairs",
                style: {
                    color: colors.text.primary
                }
            }
        },
        yaxis: {
            ...commonChartConfig.yaxis,
            title: { 
                text: "Price",
                style: {
                    color: colors.text.primary
                }
            }
        },
        annotations: {
            yaxis: keyLevels.map(item => ({
                y: item.key_level,
                borderColor: item.type === "support" ? colors.palette[0] : colors.palette[1],
                label: {
                    text: `${item.symbol} ${item.type} @ ${item.key_level}`,
                    style: {
                        color: colors.background,
                        background: item.type === "support" ? colors.palette[0] : colors.palette[1],
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
        ...commonChartConfig,
        chart: {
            ...commonChartConfig.chart,
            type: "line",
            height: 400
        },
        series: series,
        stroke: { 
            curve: "smooth", 
            width: 3,
            colors: [colors.palette[2]]
        },
        markers: {
            size: 5,
            colors: breadthSeries.map(v => v >= 50 ? colors.palette[0] : colors.palette[1]),
            strokeColors: colors.background,
            strokeWidth: 2
        },
        xaxis: {
            ...commonChartConfig.xaxis,
            title: { 
                text: "Previous Calculations",
                style: {
                    color: colors.text.primary
                }
            }
        },
        yaxis: {
            ...commonChartConfig.yaxis,
            min: 0,
            max: 100,
            title: { 
                text: "Breadth %",
                style: {
                    color: colors.text.primary
                }
            },
            labels: {
                formatter: val => `${val}%`
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
                    fillColor: colors.paletteFill[0],
                    opacity: 0.2,
                    label: {
                        text: "Bullish Zone",
                        style: {
                            color: colors.palette[0],
                            background: colors.paletteFill[0],
                            fontSize: '12px'
                        }
                    }
                },
                {
                    y: 0,
                    y2: 50,
                    fillColor: colors.paletteFill[1],
                    opacity: 0.2,
                    label: {
                        text: "Bearish Zone",
                        style: {
                            color: colors.palette[1],
                            background: colors.paletteFill[1],
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
      <span style="font-size: 1rem; color: ${btcChangePct >= 0 ? colors.palette[0] : colors.palette[1]}; font-weight: 500;">
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
    ...commonChartConfig,
    chart: {
      ...commonChartConfig.chart,
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
    colors: [colors.palette[2]],
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
    ...commonChartConfig,
    chart: { 
      ...commonChartConfig.chart,
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
            { from: -100, to: 0, color: colors.palette[1] },
            { from: 0, to: 100, color: colors.palette[0] }
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
      ...commonChartConfig.xaxis,
      title: { 
        text: "Performance (%)",
        style: {
          color: colors.text.primary
        }
      }
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
  const colors = getThemeColors();
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
    ...commonChartConfig,
    chart: {
      ...commonChartConfig.chart,
      type: "line",
      toolbar: { show: false },
      background: colors.background,
      foreColor: colors.text.primary
    },
    stroke: {
      width: 2,
      curve: 'smooth'
    },
    colors: [colors.palette[4]],
    series: series,
    xaxis: {
      ...commonChartConfig.xaxis,
      type: "datetime",
      labels: { 
        datetimeUTC: false,
      }
    },
    yaxis: {
      ...commonChartConfig.yaxis,
      min: 0,
      max: 2,
      tickAmount: 5,
      labels: {
        formatter: function(val) {
          return val.toFixed(1);
        }
      },
      title: {
        text: "Volume Ratio",
        style: {
          color: colors.text.secondary
        }
      }
    },
    tooltip: {
      ...commonChartConfig.tooltip,
      x: { format: "HH:mm" },
      y: {
        formatter: function(val) {
          return val.toFixed(2);
        }
      }
    },
    markers: {
      size: 3,
      strokeColors: colors.palette[4],
      strokeWidth: 2,
      hover: {
        size: 5
      }
    },
    annotations: {
      yaxis: [
        {
          y: 1,
          borderColor: colors.palette[0],
          label: {
            text: "Neutral (1.0)",
            style: {
              background: colors.palette[0],
              color: colors.background,
              fontSize: "12px"
            }
          }
        },
        {
          y: 1.5,
          borderColor: colors.palette[3],
          label: {
            text: "High (1.5)",
            style: {
              background: colors.palette[3],
              color: colors.background,
              fontSize: "12px"
            }
          }
        },
        {
          y: 0.5,
          borderColor: colors.palette[1],
          label: {
            text: "Low (0.5)",
            style: {
              background: colors.palette[1],
              color: colors.background,
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
  const colors = getThemeColors();
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
    { value: resistance, label: "Resistance", color: colors.palette[1] },
    { value: pivot, label: "Pivot", color: colors.palette[4] },
    { value: support, label: "Support", color: colors.palette[0] },
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
    ...commonChartConfig,
    chart: {
      ...commonChartConfig.chart,
      type: "line",
      height: 500,
      toolbar: { show: false },
      background: colors.background,
      foreColor: colors.text.primary
    },
    stroke: {
      width: [3, ...levels.map(() => 2)],
      dashArray: [0, ...levels.map(() => 4)]
    },
    colors: [colors.palette[4], ...levels.map(l => l.color)],
    series: series,
    xaxis: {
      ...commonChartConfig.xaxis,
      type: "datetime",
      labels: { 
        datetimeUTC: false,
      }
    },
    yaxis: {
      ...commonChartConfig.yaxis,
      decimalsInFloat: 4,
      labels: {
        formatter: val => val.toFixed(3),
      }
    },
    tooltip: {
      ...commonChartConfig.tooltip,
      x: { format: "HH:mm" },
    },
    annotations: {
      yaxis: levels.map(l => ({
        y: l.value,
        borderColor: l.color,
        label: {
          text: l.label + " " + l.value.toFixed(3),
          style: {
            background: l.color,
            color: colors.background,
            fontSize: "12px",
            fontWeight: "bold"
          }
        }
      }))
    },
    legend: { 
      ...commonChartConfig.legend,
      show: true,
      position: 'top',
      horizontalAlign: 'right',
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
    ...commonChartConfig,
    chart: {
      ...commonChartConfig.chart,
      type: "bar",
      toolbar: { show: false },
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: "50%",
        borderRadius: 6
      }
    },
    colors: [current >= open ? colors.palette[0] : colors.palette[1]],
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
      ...commonChartConfig.xaxis,
      categories: [data.symbol],
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: {
      ...commonChartConfig.yaxis,
      min: 0,
      max: 100,
      tickAmount: 4,
      labels: {
        formatter: val => {
          if (val === 0) return `Low: ${low}`;
          if (val === 100) return `High: ${high}`;
          return `${val}%`;
        }
      }
    },
    tooltip: {
      ...commonChartConfig.tooltip,
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
          borderColor: current >= open ? colors.palette[0] : colors.palette[1],
          label: {
            style: {
              color: colors.background,
              background: current >= open ? colors.palette[0] : colors.palette[1],
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



function renderStockCorrelationMatrix(element, sectorCorrelationMatrix) {
    const colors = getThemeColors();
    const sectors = Object.keys(sectorCorrelationMatrix);

    const series = sectors.map(rowSector => ({
        name: rowSector,
        data: sectors.map(colSector => ({
            x: colSector,
            y: sectorCorrelationMatrix[rowSector][colSector]
        }))
    }));

    const options = {
        ...commonChartConfig,
        chart: {
            ...commonChartConfig.chart,
            type: 'heatmap',
            height: 700
        },
        plotOptions: {
            heatmap: {
                shadeIntensity: 0.6,
                radius: 4,
                useFillColorAsStroke: false,
                colorScale: {
                    inverse: false,
                    ranges: [
                        { from: -1, to: -0.75, color: colors.palette[1], name: 'Very Strong Negative' },
                        { from: -0.75, to: -0.5, color: colors.palette[2], name: 'Strong Negative' },
                        { from: -0.5, to: -0.25, color: colors.paletteFill[2], name: 'Moderate Negative' },
                        { from: -0.25, to: 0, color: colors.grid, name: 'Weak Negative' },
                        { from: 0, to: 0.25, color: colors.grid, name: 'Weak Positive' },
                        { from: 0.25, to: 0.5, color: colors.paletteFill[0], name: 'Moderate Positive' },
                        { from: 0.5, to: 0.75, color: colors.palette[2], name: 'Strong Positive' },
                        { from: 0.75, to: 1, color: colors.palette[0], name: 'Very Strong Positive' }
                    ]
                }
            }
        },
        dataLabels: {
            ...commonChartConfig.dataLabels,
            enabled: true,
            formatter: (val) => val.toFixed(2),
            style: {
                ...commonChartConfig.dataLabels.style,
                fontSize: '10px'
            }
        },
        xaxis: {
            ...commonChartConfig.xaxis,
            categories: sectors,
            labels: {
                ...commonChartConfig.xaxis.labels,
                rotate: -45,
                trim: true
            },
            title: {
                text: 'Sectors',
                style: {
                    color: colors.text.primary,
                    fontSize: '14px'
                }
            }
        },
        yaxis: {
            ...commonChartConfig.yaxis,
            title: {
                text: 'Sectors',
                style: {
                    color: colors.text.primary,
                    fontSize: '14px'
                }
            }
        },
        title: {
            text: 'Sector Correlation Matrix',
            align: 'center',
            style: {
                color: colors.text.primary,
                fontSize: '18px',
                fontWeight: 'bold'
            }
        },
        tooltip: {
            ...commonChartConfig.tooltip,
            y: {
                formatter: (val) => val.toFixed(3),
                title: {
                    formatter: () => 'Correlation: '
                }
            }
        },
        series: series
    };

    // If chart already exists → update
    if (element.stockCorrChart) {
        element.stockCorrChart.updateOptions(options);
        element.stockCorrChart.updateSeries(series);
    } else {
        element.stockCorrChart = new ApexCharts(element, options);
        element.stockCorrChart.render();
    }
}















