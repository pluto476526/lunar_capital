# LunarCapital Django Application Structure


```
lunar_capital/
├── accounts/          # User authentication & profiles
├── dashboard/         # Main dashboard interface
├── market_data/       # Market data processing & storage
├── alerts/            # IFTTT alert system
├── visualization/     # Plotly chart generation
├── analysis/          # Trade logic testing & analysis
├── notifications/     # Notification system
└── api/               # REST/WebSocket endpoints
```

## Detailed App Descriptions

### 1. accounts App
- **Purpose**: User management and authentication
- **Key Models**:
  - `CustomUser` (extending Django's User model)
  - `UserProfile` (trading preferences, API keys, notification settings)
  - `Subscription` (for premium features)
- **Features**:
  - Custom authentication with trading-specific fields
  - Profile management with trading preferences
  - API key storage for market data connections

### 2. dashboard App
- **Purpose**: Main interface and layout management
- **Key Models**:
  - `DashboardLayout` (user-specific widget arrangements)
  - `Widget` (reusable dashboard components)
- **Features**:
  - Drag-and-drop dashboard customization
  - Pre-configured widget templates
  - Layout persistence across sessions

### 3. market_data App
- **Purpose**: Data acquisition, processing, and storage
- **Key Models**:
  - `Instrument` (tradable assets: stocks, forex, crypto)
  - `MarketData` (price/volume/time series data)
  - `EconomicEvent` (calendar events, news)
- **Features**:
  - Multiple data source integration (APIs, WebSocket feeds)
  - Real-time data processing pipeline
  - Data normalization and correlation calculations

### 4. alerts App
- **Purpose**: IFTTT rule engine and alert management
- **Key Models**:
  - `AlertRule` (condition definitions)
  - `Action` (actions to perform when triggered)
  - `TriggerHistory` (audit log of fired alerts)
- **Features**:
  - Visual rule builder interface
  - Complex condition evaluation engine
  - Action execution system

### 5. visualization App
- **Purpose**: Chart and graph generation using Plotly
- **Key Models**:
  - `ChartConfig` (user chart preferences)
  - `ChartTemplate` (reusable chart setups)
- **Features**:
  - Server-side Plotly graph generation
  - Real-time chart updates via WebSockets
  - Chart customization and styling

### 6. analysis App
- **Purpose**: Trade logic testing and market analysis
- **Key Models**:
  - `TradeThesis` (user's trading ideas)
  - `BacktestResult` (historical performance data)
  - `Pattern` (technical pattern definitions)
- **Features**:
  - Rapid historical analysis of trading ideas
  - Pattern recognition and statistical testing
  - Performance metrics calculation

### 7. notifications App
- **Purpose**: Cross-platform notification system
- **Key Models**:
  - `Notification` (message store)
  - `NotificationPreference` (delivery settings)
- **Features**:
  - Multiple delivery channels (in-app, email, push, SMS)
  - Notification prioritization and grouping
  - Read/unread status tracking

### 8. api App
- **Purpose**: WebSocket and REST API endpoints
- **Key Features**:
  - Real-time data streaming via WebSockets
  - REST endpoints for mobile apps and third-party integration
  - Authentication and rate limiting

## Key Integration Points

1. **Real-time Data Flow**:
   - Market data → WebSocket consumers → Processing → Visualization
   
2. **Alert System Workflow**:
   - Market conditions → Rule evaluation → Action triggering → Notifications
   
3. **User Interaction Flow**:
   - Dashboard requests → Data aggregation → Visualization → Template rendering

