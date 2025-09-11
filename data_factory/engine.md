Data Factory Engine Module
Overview
The engine.py module is a core component of the data_factory package within a larger financial trading application. It processes financial market data, focusing on day trading, by normalizing OHLCV (Open, High, Low, Close, Volume) data, calculating technical indicators, and generating market-wide metrics. The module supports multiple asset classes (stocks, forex, crypto) and intraday timeframes (1m, 5m, 15m, 30m, 1h). It integrates caching (Redis or in-memory LRU), news processing, and robust error handling to ensure reliable operation within the application.
The module serves as a backend processing engine, providing structured data and analytics for trading strategies, dashboards, or algorithmic trading systems. It interacts with other application components, such as data ingestion pipelines and news processors, to deliver comprehensive market insights.
Functionality
The module performs the following key tasks:

Caching: Stores and retrieves data using Redis or an in-memory LRU cache to optimize performance.
Data Normalization: Standardizes OHLCV data from various sources for consistent processing.
Technical Indicators: Calculates indicators like RSI, MACD, Bollinger Bands, ATR, VWAP, and pivot points, tailored for day trading.
Market-Wide Metrics: Analyzes market breadth, liquidity, volatility, and correlations across assets.
News Integration: Categorizes news by asset class, leveraging an external news_processor module.
Day Trading Focus: Provides intraday metrics, such as opening range and volume spikes, to support short-term trading strategies.

Functions
Caching

cache_set(key: str, value: Any, ttl: Optional[int]) -> None: Stores data in Redis or an in-memory LRU cache with a specified time-to-live (TTL, default 300 seconds). Serializes values to JSON for compatibility.
cache_get(key: str, default=None) -> Any: Retrieves cached data, returning the default value if the key is missing or expired. Handles Redis and in-memory cache seamlessly.

Data Normalization

normalize_ohlcv_data(values: List[Dict[str, Any]]) -> pd.DataFrame: Converts raw OHLCV data into a standardized pandas.DataFrame, ensuring consistent datetime and numeric columns (open, high, low, close, volume). Validates required columns and sorts data chronologically.
format_asset_data(api_response: Dict[str, Any], symbols: List[str]) -> Dict[str, Any]: Formats API responses into a structured dictionary, mapping case-insensitive symbols to OHLCV data and status.

Technical Indicators

safe_talib_calculation(func, default, *args, **kwargs): Wraps TA-Lib functions with error handling, returning a default value if calculations fail.
calculate_rsi(prices: np.ndarray, period: int = 9, **kwargs) -> float: Calculates the Relative Strength Index (RSI) for a price series.
calculate_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 10, **kwargs) -> float: Calculates the Average True Range (ATR) for volatility analysis.
calculate_macd(prices: np.ndarray, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9, **kwargs) -> Tuple[float, float, float]: Calculates MACD, signal line, and histogram.
calculate_bollinger_bands(prices: np.ndarray, period: int = 20, nbdev: int = 2, **kwargs) -> Tuple[float, float, float]: Calculates Bollinger Bands (upper, middle, lower).
calculate_obv(closes: np.ndarray, volumes: np.ndarray, **kwargs) -> float: Calculates On Balance Volume (OBV).
calculate_adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 10, **kwargs) -> float: Calculates the Average Directional Index (ADX) for trend strength.
calculate_standard_pivot_points(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, float]: Calculates pivot points (pivot, R1-R3, S1-S3) using the previous period’s data.
calculate_vwap(highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> float: Calculates the Volume Weighted Average Price (VWAP) for intraday trading.
calculate_opening_range(df: pd.DataFrame, timeframe: str) -> Tuple[float, float]: Calculates the high/low of the first 30 minutes (or equivalent) for a given timeframe.
calculate_intraday_metrics(df: pd.DataFrame, timeframe: str) -> Dict[str, Any]: Computes intraday metrics like range percentage, volume spike, and change from open.
calculate_technical_indicators(data: List[Dict], symbol: str, timeframe: str = '1h', rsi_period: int = 9, **kwargs) -> Dict[str, Any]: Combines all technical indicators for a symbol, including trend analysis and support/resistance levels.

Market-Wide Metrics

calculate_market_breadth(asset_data: Dict[str, Any]) -> Dict[str, Any]: Measures the percentage of bullish assets to assess market sentiment.
append_breadth_series(breadth_pct: float, maxlen: int = 20, key: str = "breadth_series") -> List[float]: Tracks market breadth over time, maintaining a fixed-length series.
get_market_session(timezone: str = "UTC") -> str: Identifies the current trading session (Asia, Europe, US, After Hours, Closed) based on the specified time zone.
get_session_activity(asset_data: Dict[str, Any]) -> str: Evaluates market activity (e.g., High, Low) based on volume ratios.
calculate_market_liquidity(asset_data: Dict[str, Any]) -> Dict[str, Any]: Assesses market liquidity using volume ratios and price stability.
get_top_movers(asset_data: Dict[str, Any], top_n: int = 5, by: str = "change_pct", timeframe: str = '1h') -> Dict[str, List[Dict[str, Any]]]: Identifies top gainers and losers based on price change or range.
calculate_volatility_index(asset_data: Dict[str, Any], period: int = 10) -> float: Computes a volatility index using ATR across assets.
technical_breadth_summary(asset_data: Dict[str, Any], asset_class: str = None) -> Dict[str, int]: Summarizes technical indicators (e.g., MACD bullish crosses, RSI overbought) across assets.
calculate_correlation_matrix(asset_data: Dict[str, Any]) -> Dict[str, Any]: Computes a correlation matrix for asset price movements.
calculate_index_returns(asset_data: Dict[str, Any], index_symbols: List[str]) -> Dict[str, Any]: Calculates daily and intraday returns for major indices (e.g., SPY, QQQ).

News Integration

get_categorized_news(raw_news: Dict[str, Any], ttl: int) -> Dict[str, list[dict]]: Categorizes news by asset class using an external news_processor, caching results for efficiency.

Main Processing

process_asset_data(asset_data: Dict[str, Any], asset_class: str, timeframe: str = '1h', news_data: Optional[Dict[str, Any]] = None, breadth_series_len: int = 20, top_n: int = 5) -> Dict[str, Any]: Generates comprehensive market metrics, including breadth, liquidity, top movers, and news.
get_asset_overview(asset_data: Dict[str, Any], symbol: str, timeframe: str = '1h') -> Dict[str, Any]: Provides a detailed overview for a single asset, combining technical indicators and market context.

Role in the Larger Application
The engine.py module acts as the analytical core of the trading application, processing raw market data and news to produce actionable insights. It integrates with:

Data Ingestion: Consumes OHLCV data from APIs or databases, normalizing it for analysis.
News Processing: Works with the news_processor module to incorporate market news.
Frontend or Trading Systems: Supplies metrics and indicators to dashboards, trading algorithms, or alerting systems.
Caching Infrastructure: Leverages Redis or in-memory caching to optimize performance for real-time applications.

The module’s outputs (e.g., technical indicators, market breadth, top movers) can drive trading decisions, portfolio monitoring, or market visualization within the application.
Notes

Asset Classes: Supports stocks, forex, and crypto with asset-specific parameters (e.g., shorter MACD periods for forex).
Timeframes: Optimized for intraday trading (1m, 5m, 15m, 30m, 1h). Custom timeframes require additional configuration.
Error Handling: Robustly handles invalid inputs, missing data, and external service failures (e.g., Redis, news processor).
Dependencies: Requires numpy, pandas, talib, redis-py, cachetools, and django for settings.

