-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

------------------------------
-- 1. Market Data Table
------------------------------
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DECIMAL(15,6),
    high DECIMAL(15,6),
    low DECIMAL(15,6),
    close DECIMAL(15,6),
    volume BIGINT,

    -- Metrics
    gap_pct DECIMAL(15,6),
    price_change_pct DECIMAL(15,6),
    sma_5 DECIMAL(15,6),
    sma_10 DECIMAL(15,6),
    sma_20 DECIMAL(15,6),
    rsi DECIMAL(15,6),
    macd DECIMAL(15,6),
    macd_signal DECIMAL(15,6),
    macd_histogram DECIMAL(15,6),
    bb_upper DECIMAL(15,6),
    bb_middle DECIMAL(15,6),
    bb_lower DECIMAL(15,6),
    adx DECIMAL(15,6),
    obv DECIMAL(15,6),
    trend_direction TEXT,
    trend_strength DECIMAL(15,6),
    support_level DECIMAL(15,6),
    resistance_level DECIMAL(15,6),
    price_proximity DECIMAL(15,6),
    volume_ratio DECIMAL(15,6),
    atr DECIMAL(15,6),
    atr_ratio DECIMAL(15,6),
    pivot_points JSONB,
    vwap DECIMAL(15,6),
    opening_range_high DECIMAL(15,6),
    opening_range_low DECIMAL(15,6),
    or_breakout TEXT
);

-- Convert to hypertable
SELECT create_hypertable(
    'market_data', 
    'time',
    chunk_time_interval => INTERVAL '1 day'
);

-- Indexes
CREATE INDEX idx_market_data_symbol_time ON market_data (symbol, time DESC);
CREATE INDEX idx_market_data_time ON market_data (time DESC);

-- Compression (older than 1 month)
ALTER TABLE market_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);
SELECT add_compression_policy('market_data', INTERVAL '1 month');
SELECT add_retention_policy('market_data', INTERVAL '5 years');

------------------------------
-- 2. Market Metrics Table
------------------------------
CREATE TABLE market_metrics (
    time TIMESTAMPTZ NOT NULL,
    market TEXT NOT NULL,
    symbols JSONB,
    market_status TEXT,
    breadth_pct DECIMAL(15,6),
    breadth_series JSONB,
    volatility_index DECIMAL(15,6),
    market_liquidity JSONB,
    current_session TEXT,
    session_activity TEXT,
    top_movers JSONB,
    tech_indicators JSONB,
    corr_matrix JSONB,
    index_returns JSONB,
    news JSONB,
    narrative JSONB
);

-- Convert to hypertable
SELECT create_hypertable(
    'market_metrics', 
    'time',
    chunk_time_interval => INTERVAL '7 days'
);

-- Indexes
CREATE INDEX idx_market_metrics_market_time ON market_metrics (market, time DESC);

-- JSONB GIN indexes for faster queries
CREATE INDEX idx_market_metrics_top_movers ON market_metrics USING gin (top_movers jsonb_path_ops);
CREATE INDEX idx_market_metrics_tech_indicators ON market_metrics USING gin (tech_indicators jsonb_path_ops);
CREATE INDEX idx_market_metrics_corr_matrix ON market_metrics USING gin (corr_matrix jsonb_path_ops);

------------------------------
-- 3. Performance Metrics Table
------------------------------
CREATE TABLE performance_metrics (
    time TIMESTAMPTZ NOT NULL,
    report_id TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    total_trades INT,
    total_buys INT,
    total_sells INT,
    total_volume DECIMAL(10,6),
    trade_value DECIMAL(10,6),
    win_rate DECIMAL(10,6),
    avg_win DECIMAL(10,6),
    avg_loss DECIMAL(10,6),
    largest_win DECIMAL(10,6),
    largest_loss DECIMAL(10,6),
    profit_factor DECIMAL(10,6),
    expectancy DECIMAL(10,6),
    sharpe_ratio DECIMAL(10,6),
    max_drawdown FLOAT8,
    val_at_risk FLOAT8,
    symbols JSONB,
    equity_curve JSONB,
);

-- Convert to hypertable
SELECT create_hypertable(
    'performance_metrics', 
    'time',
    chunk_time_interval => INTERVAL '1 month'
);

-- Index
CREATE INDEX idx_performance_metrics_id_time ON performance_metrics (report_id, time DESC);

------------------------------
-- 4. Permissions
------------------------------
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pluto;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pluto;







-- psql -U your_username -d your_database -f your_schema.sql
-- psql -U pluto -d ohlcv_data -f schema_setup.sql

