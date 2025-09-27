-- schema_setup.sql
-- pkibuka@milky-way.space

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

------------------------------
-- 1. FX OHLCV Data Table
------------------------------
CREATE TABLE fx_ohlcv_data (
    symbol TEXT NOT NULL,
    time  TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    vwap DOUBLE PRECISION,
    transactions BIGINT,
    PRIMARY KEY (symbol, time)
);

SELECT create_hypertable('fx_ohlcv_data', 'time', 'symbol', number_partitions => 4);

CREATE INDEX idx_fx_ohlcv_symbol_time ON fx_ohlcv_data (symbol, time DESC);

ALTER TABLE fx_ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('fx_ohlcv_data', INTERVAL '7 days');
SELECT add_retention_policy('fx_ohlcv_data', INTERVAL '1 year');


------------------------------
-- 2. Crypto OHLCV Data Table
------------------------------
CREATE TABLE crypto_ohlcv_data (
    symbol TEXT NOT NULL,
    time  TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (symbol, time)
);

SELECT create_hypertable('crypto_ohlcv_data', 'time', 'symbol', number_partitions => 4);

CREATE INDEX idx_crypto_ohlcv_symbol_time ON crypto_ohlcv_data (symbol, time DESC);

ALTER TABLE crypto_ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('crypto_ohlcv_data', INTERVAL '7 days');
SELECT add_retention_policy('crypto_ohlcv_data', INTERVAL '1 year');


------------------------------
-- 3. Stock OHLCV Data Table
------------------------------
CREATE TABLE stock_ohlcv_data (
    symbol TEXT NOT NULL,
    time  TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    PRIMARY KEY (symbol, time)
);

SELECT create_hypertable('stock_ohlcv_data', 'time', 'symbol', number_partitions => 4);

CREATE INDEX idx_stock_ohlcv_symbol_time ON stock_ohlcv_data (symbol, time DESC);

ALTER TABLE stock_ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'time DESC',
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('stock_ohlcv_data', INTERVAL '7 days');
SELECT add_retention_policy('stock_ohlcv_data', INTERVAL '1 year');


------------------------------
-- 4. Symbol Metrics Data Table
------------------------------
CREATE TABLE symbol_metrics_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,

    -- Metrics
    gap_pct DOUBLE PRECISION,
    price_change_pct DOUBLE PRECISION,
    sma_5 DOUBLE PRECISION,
    sma_10 DOUBLE PRECISION,
    sma_20 DOUBLE PRECISION,
    rsi DOUBLE PRECISION,
    macd DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    macd_histogram DOUBLE PRECISION,
    bb_upper DOUBLE PRECISION,
    bb_middle DOUBLE PRECISION,
    bb_lower DOUBLE PRECISION,
    adx DOUBLE PRECISION,
    obv DOUBLE PRECISION,
    trend_direction TEXT,
    trend_strength DOUBLE PRECISION,
    support_level DOUBLE PRECISION,
    resistance_level DOUBLE PRECISION,
    price_proximity DOUBLE PRECISION,
    volume_ratio DOUBLE PRECISION,
    atr DOUBLE PRECISION,
    atr_ratio DOUBLE PRECISION,
    pivot_points JSONB,
    vwap DOUBLE PRECISION,
    opening_range_high DOUBLE PRECISION,
    opening_range_low DOUBLE PRECISION,
    or_breakout TEXT,
    PRIMARY KEY (time, symbol)
);

SELECT create_hypertable(
    'symbol_metrics_data', 
    'time',
    chunk_time_interval => INTERVAL '1 day'
);

CREATE INDEX idx_symbol_metrics_symbol_time ON symbol_metrics_data (symbol, time DESC);
CREATE INDEX idx_symbol_metrics_time ON symbol_metrics_data (time DESC);

ALTER TABLE symbol_metrics_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('symbol_metrics_data', INTERVAL '1 month');
SELECT add_retention_policy('symbol_metrics_data', INTERVAL '5 years');


------------------------------
-- 5. Market Metrics Table
------------------------------
CREATE TABLE market_metrics_data (
    time TIMESTAMPTZ NOT NULL,
    asset_class TEXT NOT NULL,
    symbols JSONB,
    market_status TEXT,
    breadth_pct DOUBLE PRECISION,
    breadth_series JSONB,
    volatility_index DOUBLE PRECISION,
    market_liquidity JSONB,
    current_session TEXT,
    session_activity TEXT,
    top_movers JSONB,
    tech_indicators JSONB,
    corr_matrix JSONB,
    index_returns JSONB,
    news JSONB,
    narrative JSONB,
    PRIMARY KEY (time, asset_class)
);

SELECT create_hypertable(
    'market_metrics_data', 
    'time',
    chunk_time_interval => INTERVAL '7 days'
);

CREATE INDEX idx_market_metrics_market_time ON market_metrics_data (asset_class, time DESC);

-- JSONB GIN indexes
CREATE INDEX idx_market_metrics_top_movers ON market_metrics_data USING gin (top_movers jsonb_path_ops);
CREATE INDEX idx_market_metrics_tech_indicators ON market_metrics_data USING gin (tech_indicators jsonb_path_ops);
CREATE INDEX idx_market_metrics_corr_matrix ON market_metrics_data USING gin (corr_matrix jsonb_path_ops);

ALTER TABLE market_metrics_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_class'
);

SELECT add_compression_policy('market_metrics_data', INTERVAL '1 month');
SELECT add_retention_policy('market_metrics_data', INTERVAL '5 years');


------------------------------
-- 6. Permissions
------------------------------
GRANT USAGE ON SCHEMA public TO pluto;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pluto;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO pluto;



-- psql -U your_username -d your_database -f your_schema.sql
-- psql -U pluto -d lunar_capital -f schema_setup.sql

