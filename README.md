# LunarCapital: Trading Co-Pilot Dashboard

## 🌌 Overview

LunarCapital is a revolutionary trading co-pilot dashboard designed to transform how traders interact with market data. Hosted at `milkyway.space`, this Django-powered application serves as a contextual trading assistant that reduces cognitive load and enhances decision-making through intelligent data synthesis.

> **Navigate the markets like navigating the stars** - with precision, context, and confidence.

## ✨ Key Features

### 🤖 Dynamic Market Intelligence
- Real-time, rule-based market summaries that read like expert analysis
- Contextual narratives instead of raw data tables
- Customizable alerting system with multi-condition rules

### ⚡ Real-Time Visualization
- Server-rendered Plotly graphs with WebSocket updates
- Interactive, responsive market visualizations
- Session heatmaps with volatility-based coloring

### 🎯 Trade Logic Validation
- Instant historical performance analysis for trading ideas
- Quick "sanity check" before entering positions
- Statistical win rate and P/L analysis

### 🔔 Advanced Alert System
- IFTTT (If-This-Then-That) rule engine
- Multi-condition market event detection
- Cross-platform notifications (browser, mobile, audio)

## 🚀 Why LunarCapital?

Traders currently face:

- **Information overload** from multiple screens and data sources
- **Missed opportunities** due to cognitive load limitations
- **Error-prone decision making** from disconnected analytics

LunarCapital solves these challenges by:

1. **Synthesizing** disparate data into actionable intelligence
2. **Contextualizing** market movements with narrative explanations
3. **Validating** trading ideas with historical perspective
4. **Alerting** proactively to critical market conditions

## 🛠 Technology Stack

- **Backend**: Django with Django Channels
- **Visualization**: Plotly (server-side rendering)
- **Real-time Updates**: WebSockets
- **Database**: PostgreSQL with TimescaleDB extension
- **Task Queue**: Celery with Redis
- **Deployment**: Docker & Kubernetes on MilkyWay.space

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/pluto476526/lunar_capital.git
cd lunar_capital

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## 🌐 Deployment

LunarCapital is designed for deployment on MilkyWay.space:

```yaml
# Example Kubernetes configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stellartrader
  namespace: trading
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: stellartrader-app
        image: stellartrader/app:latest
        ports:
        - containerPort: 8000
```

## 📈 Usage Examples

### Market Summary Rule
```python
# Example rule for EURUSD analysis
{
  "conditions": [
    {"metric": "price", "operator": ">", "value": "1.2000", "instrument": "EURUSD"},
    {"metric": "volume", "operator": ">", "value": "1.5*avg_20d", "instrument": "EURUSD"}
  ],
  "template": ""
}
```

### Multi-condition Alert
```python
# Alert for volatility expansion
IF VIX > 20 AND 
   SPY_volume > 1.5*20d_avg AND 
   USDJPY_1h_ATR > 0.8*24h_avg
THEN 
   notify_mobile("Volatility Expansion")
   highlight_chart("USDJPY", "red")
   play_sound("alert_warning")
```

## ⭐ Support

If you find StellarTrader helpful, please give us a star on GitHub! For support and questions:

- 📧 Email: pkibuka@milkyway.space

## 🔭 Vision

At milkyway.space, we believe trading technology should elevate human intelligence, not replace it. LunarCapital is our first step toward creating a suite of tools that make sophisticated market analysis accessible to all traders, regardless of experience level.

---

**Navigate the markets with celestial precision** ✨

*LunarCapital - Your co-pilot in the financial universe*
