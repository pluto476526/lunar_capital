## data_factory/performance_metrics.py
## pkibuka@milky-way.space

import pandas as pd
import numpy as np
import json, logging

logger = logging.getLogger(__name__)

class TradingPerformanceAnalyzer:
    def __init__(self, csv_path, initial_capital=10000, base_currency="GBP"):
        """
        Analyzer for trading performance with optional base currency conversion.

        fx_rates: dict of conversion rates to base currency, e.g. {"CAD": 0.54, "AUD": 0.49, "GBP": 1.0}
        """
        self.csv_path = csv_path
        self.initial_capital = initial_capital
        self.base_currency = base_currency
        self.fx_rates = {"USD":"1.1648","JPY":"128.30","GBP":"0.87663","CHF":"1.1534","AUD":"1.5681","CAD":"1.5459","MXN":"23.5466","NZD":"1.6880","ZAR":"15.7165"}
        self.df = None

        self.load_data()
        self.preprocess_data()
        # self.extract_fx_rates() from a json external file
        self.convert_to_base_currency()
        self.calculate_equity_curve()
        self.calculate_metrics()

    def load_data(self):
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-16')
        except UnicodeDecodeError:
            self.df = pd.read_csv(self.csv_path, encoding='ISO-8859-1')

    def preprocess_data(self):
        """Normalize ledger data into structured format."""
        # Ensure date column is properly parsed
        self.df['date'] = pd.to_datetime(self.df['Transaction Date'], dayfirst=True, errors='coerce')

        # Extract currency pair from Description
        extracted = self.df['Description'].str.extract(r'([A-Z]{3}/[A-Z]{3})')
        self.df['symbol'] = extracted[0] if not extracted.empty else pd.Series([None] * len(self.df), index=self.df.index)
        
        # Fill missing symbols from Action where applicable
        action_extracted = self.df['Action'].str.extract(r'([A-Z]{3}/[A-Z]{3})')
        self.df['symbol'] = self.df['symbol'].fillna(action_extracted[0])

        # Side mapping
        self.df['side'] = self.df['Action'].map({
            'Trade Receivable': 'buy',
            'Trade Payable': 'sell',
            'Fund receivable': 'credit',
            'Fund payable': 'debit'
        })
        
        # Numeric conversions
        self.df['quantity'] = pd.to_numeric(self.df['Amount'], errors='coerce').fillna(0)
        self.df['opening_price'] = pd.to_numeric(self.df['Opening'], errors='coerce')
        self.df['closing_price'] = pd.to_numeric(self.df['Closing'], errors='coerce')
        self.df['pnl'] = pd.to_numeric(self.df['P/L'], errors='coerce').fillna(0)
        self.df['balance'] = pd.to_numeric(self.df['Balance'], errors='coerce').fillna(0)
        self.df['currency'] = self.df['Currency'].astype(str)  # Ensure currency is string
        
        # Check for non-numeric values in critical columns
        if self.df['closing_price'].isna().any():
            self.df['closing_price'] = self.df['closing_price'].fillna(0)  # Fill NaN with 0 for trade_value
        
        # Calculate trade value
        self.df['trade_value'] = self.df['quantity'] * self.df['closing_price']
        
        logger.info("Preprocessing completed.")


    def convert_to_base_currency(self):
        """
        Convert PnL, balances, and trade values into base currency using FX rates.
        Vectorized for speed and stability.
        """        
        # Ensure FX rates are numeric
        fx_rates_numeric = {k: float(v) for k, v in self.fx_rates.items()}
        
        # Compute conversion factor for each row
        def compute_rate(currency):
            if currency == self.base_currency:
                return 1.0
            return fx_rates_numeric.get(currency, 1.0) / fx_rates_numeric.get(self.base_currency, 1.0)
        
        # Ensure currency is a Series
        if isinstance(self.df['currency'], pd.Series):
            self.df['conversion_rate'] = self.df['currency'].map(compute_rate)
        
        # Convert numeric columns
        self.df['pnl_base'] = self.df['pnl'].fillna(0) * self.df['conversion_rate']
        self.df['balance_base'] = self.df['balance'].fillna(0) * self.df['conversion_rate']
        self.df['trade_value_base'] = self.df['trade_value'].fillna(0) * self.df['conversion_rate']
        
        # Drop helper column
        self.df.drop(columns=['conversion_rate'], inplace=True)
        
        logger.info("Currency conversion completed.")


    def calculate_metrics(self):
        """
        Core performance metrics using base currency
        """
        trades = self.df[self.df['side'].isin(['buy', 'sell'])]

        self.total_trades = len(trades)
        self.total_buys = (trades['side'] == 'buy').sum()
        self.total_sells = (trades['side'] == 'sell').sum()
        self.total_volume = trades['quantity'].sum()
        self.total_value = trades['trade_value_base'].sum()  # use converted trade value

        # Win/loss using base currency
        winning = trades[trades['pnl_base'] > 0]
        losing = trades[trades['pnl_base'] < 0]

        self.win_rate = len(winning) / self.total_trades if self.total_trades else 0
        self.average_win = winning['pnl_base'].mean() if not winning.empty else 0
        self.average_loss = losing['pnl_base'].mean() if not losing.empty else 0
        self.largest_win = winning['pnl_base'].max() if not winning.empty else 0
        self.largest_loss = losing['pnl_base'].min() if not losing.empty else 0

        # Profit factor
        gross_profit = winning['pnl_base'].sum()
        gross_loss = abs(losing['pnl_base'].sum()) if not losing.empty else 1
        self.profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

        # Expectancy
        self.expectancy = (self.win_rate * self.average_win) - ((1 - self.win_rate) * abs(self.average_loss))

        # Sharpe ratio using base currency
        daily_returns = trades.groupby('date')['pnl_base'].sum()
        risk_free = 0.02 / 252
        excess = daily_returns - risk_free
        self.sharpe_ratio = excess.mean() / excess.std() if excess.std() else 0

        # Risk metrics
        self.max_drawdown = self.calculate_max_drawdown()
        self.var_95 = np.percentile(trades['pnl_base'], 5) if not trades.empty else 0

        # Symbol-level performance in base currency
        self.symbol_performance = (
            trades.groupby('symbol')['pnl_base']
            .agg(['count', 'sum', 'mean', 'max', 'min'])
            .rename(columns={
                'count': 'trade_count',
                'sum': 'total_pnl',
                'mean': 'avg_pnl',
                'max': 'best_trade',
                'min': 'worst_trade'
            })
            .sort_values('total_pnl', ascending=False)
            .reset_index()
            .to_dict(orient='records')
        )


    def calculate_equity_curve(self):
        """Build equity curve using base currency PnL."""
        initial_capital = self.initial_capital
        daily_pnl = self.df.groupby('date')['pnl_base'].sum().reset_index()
        daily_pnl = daily_pnl.sort_values('date')
        daily_pnl['cumulative_pnl'] = daily_pnl['pnl_base'].cumsum()
        daily_pnl['equity'] = initial_capital + daily_pnl['cumulative_pnl']
        daily_pnl['return'] = daily_pnl['equity'].pct_change().fillna(0)
        daily_pnl['cumulative_return'] = (1 + daily_pnl['return']).cumprod() - 1
        self.equity_curve = daily_pnl


    def calculate_max_drawdown(self):
        if not hasattr(self, 'equity_curve'):
            return 0
        cumulative = self.equity_curve['cumulative_return']
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()


    def generate_report(self):
        """
        Return dictionary with all metrics and symbol-level performance in base currency
        """
        return {
            "Base Currency": self.base_currency,
            "Summary": {
                "Total Trades": self.total_trades,
                "Total Buys": self.total_buys,
                "Total Sells": self.total_sells,
                "Total Volume": self.total_volume,
                "Total Trade Value (Base)": self.total_value,
            },
            "Performance": {
                "Win Rate %": round(self.win_rate * 100, 2),
                "Average Win (Base)": self.average_win,
                "Average Loss (Base)": self.average_loss,
                "Largest Win (Base)": self.largest_win,
                "Largest Loss (Base)": self.largest_loss,
                "Profit Factor": self.profit_factor,
                "Expectancy (Base)": self.expectancy,
                "Sharpe Ratio": self.sharpe_ratio,
            },
            "Risk": {
                "Max Drawdown": self.max_drawdown,
                "Value at Risk (95%) (Base)": self.var_95,
            },
            "Symbols": self.symbol_performance,
            "EquityCurve": self.equity_curve.to_dict(orient='records'),
        }

    def export_report(self, filename="trading_performance_report.txt", fmt="txt"):
        """
        Export the performance report to a file (txt or json)
        """
        report = self.generate_report()

        if fmt == "json":
            with open(filename.replace(".txt", ".json"), "w") as f:
                json.dump(report, f, indent=4, default=str)
            print(f"Report exported to {filename.replace('.txt', '.json')}")
            return

        # Default = text format
        def write_section(f, section, data, indent=0):
            prefix = " " * indent
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        f.write(f"{prefix}{key}:\n")
                        write_section(f, key, value, indent + 4)
                    else:
                        f.write(f"{prefix}{key}: {value}\n")
            elif isinstance(data, list):
                for i, item in enumerate(data, 1):
                    f.write(f"{prefix}- Item {i}:\n")
                    write_section(f, f"Item {i}", item, indent + 4)
            else:
                f.write(f"{prefix}{data}\n")

        with open(filename, "w") as f:
            f.write("TRADING PERFORMANCE REPORT\n")
            f.write("=" * 50 + "\n\n")

            for section, metrics in report.items():
                f.write(f"{section}:\n")
                f.write("-" * len(section) + "\n")
                write_section(f, section, metrics, indent=2)
                f.write("\n")

        print(f"Report exported to {filename}")




