import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd
import psycopg2

from decouple import config

logger = logging.getLogger(__name__)


class DataIngestor:
    def __init__(
        self,
        dbname: str = config("DB_NAME"),
        user: str = config("DB_USER"),
        password: str = config("DB_PASS"),
        host: str = "localhost",
    ):
        self.conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host
        )
        self.cursor = self.conn.cursor()
        logger.warning("DataIngestor connected to database")

    def insert_fx_ohlcv_data(
        self, data: Dict[str, List[Dict[str, Any]]], batch_size: int = 1000
    ) -> None:
        """
        Efficiently insert FX OHLCV data into fx_ohlcv_data hypertable.

        Data is inserted in batches per symbol to reduce memory and transaction overhead.
        Timestamps are converted from milliseconds to PostgreSQL TIMESTAMP.

        Args:
            data: Dictionary of symbols mapping to list of OHLCV dicts.
                  Example:
                  {
                      "EUR/CAD": [{"timestamp": 1756252800000, "open": 1.23, "high": 1.24, ...}, ...],
                      "USD/JPY": [...],
                  }
            batch_size: Number of rows to insert per batch.
        """
        if not data:
            return

        try:
            for symbol, ohlc_list in data.items():
                # Prepare tuples for insertion
                rows = [
                    (
                        symbol,
                        datetime.utcfromtimestamp(
                            row["timestamp"] / 1000
                        ),  # convert ms -> datetime
                        row["open"],
                        row["high"],
                        row["low"],
                        row["close"],
                        row["volume"],
                        row["vwap"],
                        row["transactions"],
                    )
                    for row in ohlc_list
                ]

                # Insert in batches
                for i in range(0, len(rows), batch_size):
                    batch = rows[i : i + batch_size]
                    query = """
                        INSERT INTO fx_ohlcv_data
                        (symbol, time, open, high, low, close, volume, vwap, transactions)
                        VALUES %s
                        ON CONFLICT (symbol, time) DO NOTHING
                    """
                    psycopg2.extras.execute_values(self.cursor, query, batch)

                logger.warning(f"Inserted {len(rows)} rows for symbol {symbol}")

            # Commit once per call
            self.conn.commit()

        except Exception as e:
            logger.error(f"FX data not saved: {e}")
            self.conn.rollback()

    def insert_stock_ohlcv_data(self, data):
        pass

    def insert_crypto_ohlcv_data(self, data):
        pass

    def insert_market_metrics_data(self, data: Dict[str, Any]) -> None:
        """
        Inserts a single market-wide metrics snapshot (fx, crypto, stocks) into the database.
        """
        if not data:
            return

        try:
            query = """
                INSERT INTO market_metrics_data (
                    time,
                    asset_class,
                    symbols,
                    market_status,
                    breadth_pct,
                    breadth_series,
                    volatility_index,
                    market_liquidity,
                    current_session,
                    session_activity,
                    top_movers,
                    tech_indicators,
                    corr_matrix,
                    index_returns,
                    news,
                    narrative
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (time, asset_class) DO UPDATE
                SET
                    symbols = EXCLUDED.symbols,
                    market_status = EXCLUDED.market_status,
                    breadth_pct = EXCLUDED.breadth_pct,
                    breadth_series = EXCLUDED.breadth_series,
                    volatility_index = EXCLUDED.volatility_index,
                    market_liquidity = EXCLUDED.market_liquidity,
                    current_session = EXCLUDED.current_session,
                    session_activity = EXCLUDED.session_activity,
                    top_movers = EXCLUDED.top_movers,
                    tech_indicators = EXCLUDED.tech_indicators,
                    corr_matrix = EXCLUDED.corr_matrix,
                    index_returns = EXCLUDED.index_returns,
                    news = EXCLUDED.news,
                    narrative = EXCLUDED.narrative;
            """

            # Prepare values for SQL insertion
            # Wrap JSON fields using psycopg2.extras.Json
            values = (
                datetime.utcnow(),
                data.get(
                    "asset_class",
                ),
                psycopg2.extras.Json(data.get("symbols", [])),
                data.get("market_status"),
                data.get("breadth_pct"),
                psycopg2.extras.Json(data.get("breadth_series", [])),
                data.get("volatility_index"),
                psycopg2.extras.Json(data.get("market_liquidity", {})),
                data.get("current_session"),
                data.get("session_activity"),
                psycopg2.extras.Json(data.get("top_movers", {})),
                psycopg2.extras.Json(data.get("technical_breadth", {})),
                psycopg2.extras.Json(data.get("correlation_matrix", {})),
                psycopg2.extras.Json(data.get("index_returns", {})),
                psycopg2.extras.Json(data.get("news", [])),
                psycopg2.extras.Json(data.get("narrative", {})),
            )

            # Execute the SQL query with the values
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                self.conn.commit()

        except Exception as e:
            logger.error(f"Market metrics data not saved: {e}")
            self.conn.rollback()


    def insert_symbol_metrics_data(self, data: Dict[str, Any]) -> None:
        """
        Insert a single symbol metrics row into `symbol_metrics_data`.

        Args:
            data (Dict[str, Any]): Symbol metrics dictionary containing all columns.
        """
        if not data:
            return

        try:
            # Prepare row mapping all fields explicitly
            row = (
                data['timestamp'],
                data['symbol'],
                data.get('open', None),
                data.get('high', None),
                data.get('low', None),
                data.get('close', None),
                data.get('volume', None),
                data.get('gap_pct', None),
                data.get('price_change_pct', None),
                data.get('sma_5', None),
                data.get('sma_10', None),
                data.get('sma_20', None),
                data.get('rsi', None),
                data.get('macd', None),
                data.get('macd_signal', None),
                data.get('macd_histogram', None),
                data.get('bollinger_upper', None),
                data.get('bollinger_middle', None),
                data.get('bollinger_lower', None),
                data.get('adx', None),
                data.get('obv', None),
                data.get('trend_direction', None),
                data.get('trend_strength', None),
                data.get('support_level', None),
                data.get('resistance_level', None),
                data.get('price_proximity', None),
                data.get('volume_ratio', None),
                data.get('atr', None),
                data.get('atr_ratio', None),
                psycopg2.extras.Json(data.get('pivot_points', {})),
                data.get('vwap', None),
                data.get('opening_range_high', None),
                data.get('opening_range_low', None),
                data.get('or_breakout', None)
            )

            query = """
                INSERT INTO symbol_metrics_data (
                    time, symbol, open, high, low, close, volume,
                    gap_pct, price_change_pct, sma_5, sma_10, sma_20, rsi,
                    macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower,
                    adx, obv, trend_direction, trend_strength, support_level,
                    resistance_level, price_proximity, volume_ratio, atr, atr_ratio,
                    pivot_points, vwap, opening_range_high, opening_range_low, or_breakout
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (time, symbol) DO NOTHING
            """

            with self.conn.cursor() as cur:
                cur.execute(query, row)
                self.conn.commit()

            logger.warning(f"Inserted symbol metrics for {data['symbol']} at {data['timestamp']}")

        except Exception as e:
            logger.error(f"Symbol metrics data not saved: {e}")
            self.conn.rollback()            

        def close(self):
            self.cursor.close()
            self.conn.close()
