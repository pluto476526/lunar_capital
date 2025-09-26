import psycopg2
import pandas as pd

class FinancialAnalyzer:
    def __init__(self, dbname='financial_data', user='finance_user', 
                 password='your_secure_password', host='localhost'):
        self.conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host
        )
    
    def get_price_history(self, symbol, start_date, end_date):
        """Get price history for a symbol"""
        query = """
        SELECT time, open, high, low, close, volume
        FROM market_data
        WHERE symbol = %s AND time BETWEEN %s AND %s
        ORDER BY time DESC
        """
        return pd.read_sql_query(query, self.conn, params=(symbol, start_date, end_date))
    
    def calculate_moving_averages(self, symbol, window=20):
        """Calculate moving averages using TimescaleDB hyperfunctions"""
        query = """
        SELECT 
            time_bucket('1 day', time) as bucket,
            symbol,
            avg(close) as price,
            avg(avg(close)) OVER (ORDER BY time_bucket('1 day', time) 
                ROWS %s PRECEDING) as moving_avg
        FROM market_data
        WHERE symbol = %s
        GROUP BY bucket, symbol
        ORDER BY bucket DESC
        """
        return pd.read_sql_query(query, self.conn, params=(window, symbol))
    
    def get_strategy_metrics(self, strategy_name):
        """Get metrics for a trading strategy"""
        query = """
        SELECT time, metric_name, metric_value, parameters
        FROM trading_metrics
        WHERE strategy_name = %s
        ORDER BY time DESC
        LIMIT 1000
        """
        return pd.read_sql_query(query, self.conn, params=(strategy_name,))
    
    def close(self):
        self.conn.close()
