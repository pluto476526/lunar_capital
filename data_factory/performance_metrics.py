import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class TradingPerformanceAnalyzer:
    def __init__(self, csv_file_path):
        """
        Initialize the analyzer with CSV data
        """
        self.df = pd.read_csv(csv_file_path)
        self.preprocess_data()
        self.calculate_metrics()
        
    def preprocess_data(self):
        """
        Clean and preprocess the trading data
        """
        # Convert date column to datetime
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'])
        elif 'Date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['Date'])
        
        # Ensure necessary columns exist (customize based on your CSV structure)
        required_columns = ['symbol', 'quantity', 'price', 'side']  # Adjust based on your CSV
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"Required column '{col}' not found in CSV")
        
        # Calculate trade value
        self.df['trade_value'] = self.df['quantity'] * self.df['price']
        
        # Identify buy/sell transactions
        self.df['is_buy'] = self.df['side'].str.lower().isin(['buy', 'b'])
        self.df['is_sell'] = self.df['side'].str.lower().isin(['sell', 's'])
        
    def calculate_metrics(self):
        """
        Calculate comprehensive trading performance metrics
        """
        # Total metrics
        self.total_trades = len(self.df)
        self.total_buys = self.df['is_buy'].sum()
        self.total_sells = self.df['is_sell'].sum()
        self.total_volume = self.df['quantity'].sum()
        self.total_value = self.df['trade_value'].sum()
        
        # Win/loss metrics
        winning_trades = self.df[self.df['pnl'] > 0] if 'pnl' in self.df.columns else pd.DataFrame()
        losing_trades = self.df[self.df['pnl'] < 0] if 'pnl' in self.df.columns else pd.DataFrame()
        
        self.win_rate = len(winning_trades) / self.total_trades if self.total_trades > 0 else 0
        self.average_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        self.average_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        self.largest_win = winning_trades['pnl'].max() if len(winning_trades) > 0 else 0
        self.largest_loss = losing_trades['pnl'].min() if len(losing_trades) > 0 else 0
        
        # Profit factor
        gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 1  # Avoid division by zero
        self.profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        # Risk/reward metrics
        self.expectancy = (self.win_rate * self.average_win) - ((1 - self.win_rate) * abs(self.average_loss))
        
        # Calculate Sharpe ratio if we have enough data
        if 'pnl' in self.df.columns and 'date' in self.df.columns:
            daily_returns = self.df.groupby('date')['pnl'].sum()
            risk_free_rate = 0.02 / 252  # Assuming 2% annual risk-free rate
            excess_returns = daily_returns - risk_free_rate
            self.sharpe_ratio = excess_returns.mean() / excess_returns.std() if excess_returns.std() != 0 else 0
        
        # Holding period analysis if we have entry/exit dates
        if 'entry_date' in self.df.columns and 'exit_date' in self.df.columns:
            self.df['holding_period'] = (pd.to_datetime(self.df['exit_date']) - 
                                         pd.to_datetime(self.df['entry_date'])).dt.days
            self.avg_holding_period = self.df['holding_period'].mean()
        
    def generate_report(self):
        """
        Generate a comprehensive trading performance report
        """
        report = {
            "Summary Metrics": {
                "Total Trades": self.total_trades,
                "Total Buy Orders": self.total_buys,
                "Total Sell Orders": self.total_sells,
                "Total Volume": self.total_volume,
                "Total Trade Value": self.total_value
            },
            "Performance Metrics": {
                "Win Rate": f"{self.win_rate * 100:.2f}%",
                "Average Win": self.average_win,
                "Average Loss": self.average_loss,
                "Largest Win": self.largest_win,
                "Largest Loss": self.largest_loss,
                "Profit Factor": self.profit_factor,
                "Expectancy": self.expectancy,
                "Sharpe Ratio": self.sharpe_ratio if hasattr(self, 'sharpe_ratio') else "N/A"
            },
            "Risk Metrics": {
                "Risk of Ruin": self.calculate_risk_of_ruin(),
                "Maximum Drawdown": self.calculate_max_drawdown() if hasattr(self, 'equity_curve') else "N/A",
                "Value at Risk (95%)": self.calculate_var() if 'pnl' in self.df.columns else "N/A"
            }
        }
        
        if hasattr(self, 'avg_holding_period'):
            report["Time Metrics"] = {
                "Average Holding Period (days)": self.avg_holding_period
            }
        
        return report
    
    def calculate_risk_of_ruin(self):
        """
        Calculate risk of ruin based on win rate and average win/loss
        """
        if self.win_rate == 0 or self.average_loss == 0:
            return "N/A"
        
        # Simplified risk of ruin calculation
        risk_per_trade = abs(self.average_loss) / (self.average_win + abs(self.average_loss))
        risk_of_ruin = ((1 - risk_per_trade) / risk_per_trade) ** (self.average_win / abs(self.average_loss))
        
        return f"{risk_of_ruin * 100:.4f}%" if risk_of_ruin < 1 else "High"
    
    def calculate_max_drawdown(self):
        """
        Calculate maximum drawdown from equity curve
        """
        if not hasattr(self, 'equity_curve'):
            self.calculate_equity_curve()
        
        cumulative_returns = self.equity_curve['cumulative_return']
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()
        
        return f"{max_drawdown * 100:.2f}%"
    
    def calculate_var(self, confidence_level=0.95):
        """
        Calculate Value at Risk
        """
        if 'pnl' not in self.df.columns:
            return "N/A"
        
        var = np.percentile(self.df['pnl'], (1 - confidence_level) * 100)
        return var
    
    def calculate_equity_curve(self, initial_capital=10000):
        """
        Calculate equity curve over time
        """
        if 'date' not in self.df.columns or 'pnl' not in self.df.columns:
            return
        
        # Group P&L by date
        daily_pnl = self.df.groupby('date')['pnl'].sum().reset_index()
        daily_pnl = daily_pnl.sort_values('date')
        
        # Calculate cumulative returns
        daily_pnl['cumulative_pnl'] = daily_pnl['pnl'].cumsum()
        daily_pnl['equity'] = initial_capital + daily_pnl['cumulative_pnl']
        daily_pnl['return'] = daily_pnl['equity'].pct_change().fillna(0)
        daily_pnl['cumulative_return'] = (1 + daily_pnl['return']).cumprod() - 1
        
        self.equity_curve = daily_pnl
    
    def visualize_performance(self):
        """
        Create visualizations for trading performance
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Trading Performance Analysis', fontsize=16)
        
        # Equity curve
        if hasattr(self, 'equity_curve'):
            axes[0, 0].plot(self.equity_curve['date'], self.equity_curve['equity'])
            axes[0, 0].set_title('Equity Curve')
            axes[0, 0].set_xlabel('Date')
            axes[0, 0].set_ylabel('Equity Value')
            axes[0, 0].grid(True)
        
        # Win/Loss distribution
        if 'pnl' in self.df.columns:
            axes[0, 1].hist(self.df['pnl'], bins=30, alpha=0.7, color='skyblue')
            axes[0, 1].axvline(x=0, color='red', linestyle='--')
            axes[0, 1].set_title('Profit/Loss Distribution')
            axes[0, 1].set_xlabel('P&L')
            axes[0, 1].set_ylabel('Frequency')
        
        # Trade activity by day of week
        if 'date' in self.df.columns:
            self.df['day_of_week'] = self.df['date'].dt.day_name()
            day_counts = self.df['day_of_week'].value_counts()
            axes[1, 0].bar(day_counts.index, day_counts.values)
            axes[1, 0].set_title('Trades by Day of Week')
            axes[1, 0].set_xlabel('Day of Week')
            axes[1, 0].set_ylabel('Number of Trades')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Performance by symbol (if data available)
        if 'symbol' in self.df.columns and 'pnl' in self.df.columns:
            symbol_performance = self.df.groupby('symbol')['pnl'].sum().sort_values()
            axes[1, 1].barh(symbol_performance.index, symbol_performance.values)
            axes[1, 1].set_title('Performance by Symbol')
            axes[1, 1].set_xlabel('Total P&L')
        
        plt.tight_layout()
        plt.show()
    
    def export_report(self, filename="trading_performance_report.txt"):
        """
        Export the performance report to a text file
        """
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            f.write("TRADING PERFORMANCE REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            for section, metrics in report.items():
                f.write(f"{section}:\n")
                f.write("-" * len(section) + "\n")
                
                for metric, value in metrics.items():
                    f.write(f"{metric}: {value}\n")
                
                f.write("\n")
        
        print(f"Report exported to {filename}")

# Example usage
if __name__ == "__main__":
    # Initialize analyzer with your CSV file path
    analyzer = TradingPerformanceAnalyzer("trading_data.csv")
    
    # Generate and print report
    report = analyzer.generate_report()
    for section, metrics in report.items():
        print(section)
        print("-" * len(section))
        for metric, value in metrics.items():
            print(f"{metric}: {value}")
        print()
    
    # Create visualizations
    analyzer.visualize_performance()
    
    # Export report to file
    analyzer.export_report()
