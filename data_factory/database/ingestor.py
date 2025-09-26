import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import time

class FinancialDataIngestor:
    def __init__(self, dbname='financial_data', user='finance_user', 
                 password='your_secure_password', host='localhost'):
        self.conn = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host
        )
        self.cursor = self.conn.cursor()
    
    def insert_market_data_batch(self, df):
        """Insert batch of market data efficiently"""
        if df.empty:
            return
        
        # Convert DataFrame to list of tuples
        data_tuples = [
            (row['time'], row['symbol'], row['open'], row['high'], 
             row['low'], row['close'], row['volume'], row.get('vwap'), 
             row.get('trades'), row.get('exchange'))
            for _, row in df.iterrows()
        ]
        
        query = """
        INSERT INTO market_data 
        (time, symbol, open, high, low, close, volume, vwap, trades, exchange)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (time, symbol) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            vwap = EXCLUDED.vwap,
            trades = EXCLUDED.trades
        """
        
        self.cursor.executemany(query, data_tuples)
        self.conn.commit()
    
    def insert_trading_metrics(self, strategy_name, metric_name, value, parameters=None):
        """Insert trading strategy metrics"""
        query = """
        INSERT INTO trading_metrics 
        (time, strategy_name, metric_name, metric_value, parameters)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        self.cursor.execute(query, (datetime.now(), strategy_name, metric_name, value, parameters))
        self.conn.commit()
    
    def close(self):
        self.cursor.close()
        self.conn.close()

# Example usage
if __name__ == "__main__":
    ingestor = FinancialDataIngestor()
    
    # Example: Insert sample market data
    sample_data = pd.DataFrame({
        'time': [datetime.now() - timedelta(minutes=i) for i in range(100)],
        'symbol': ['AAPL'] * 100,
        'open': [150 + i * 0.1 for i in range(100)],
        'high': [151 + i * 0.1 for i in range(100)],
        'low': [149 + i * 0.1 for i in range(100)],
        'close': [150.5 + i * 0.1 for i in range(100)],
        'volume': [1000000] * 100
    })
    
    ingestor.insert_market_data_batch(sample_data)
    ingestor.close()
