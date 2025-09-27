DROP TABLE IF EXISTS fx_ohlcv_data CASCADE;
DROP TABLE IF EXISTS stock_ohlcv_data CASCADE;
DROP TABLE IF EXISTS crypto_ohlcv_data CASCADE;
DROP TABLE IF EXISTS market_metrics_data CASCADE;
DROP TABLE IF EXISTS symbol_metrics_data CASCADE;

\i schema_setup.sql

