# data_factory/rules_config.py
FOREX_RULES = {
    'central_bank_impact': {
        'conditions': [
            {'metric': 'price_change_pct', 'operator': '>', 'value': 2, 'lookback': 1},
            {'news_keywords': ['central bank', 'interest rates', 'policy'], 'min_articles': 2}
        ],
        'narrative': '{currency_pair} reacting to central bank policy expectations with {price_change_pct}% move',
        'priority': 'high',
        'asset_class': 'forex'
    },
    'trend_continuation': {
        'conditions': [
            {'metric': 'trend_strength', 'operator': '>', 'value': 0.7, 'lookback': 5},
            {'metric': 'volume_ratio', 'operator': '>', 'value': 1.2, 'lookback': 5}
        ],
        'narrative': '{currency_pair} showing strong {trend_direction} momentum with {trend_strength} trend strength',
        'priority': 'medium',
        'asset_class': 'forex'
    },
    'support_resistance': {
        'conditions': [
            {'metric': 'price_proximity', 'operator': '<', 'value': 0.01, 'lookback': 0},
            {'metric': 'rsi', 'operator': '<', 'value': 30, 'lookback': 0}
        ],
        'narrative': '{currency_pair} approaching key support at {support_level}, potentially oversold with RSI at {rsi}',
        'priority': 'medium',
        'asset_class': 'forex'
    },
    'breakout_alert': {
        'conditions': [
            {'metric': 'price', 'operator': '>', 'value': '1.02*resistance_level', 'lookback': 0},
            {'metric': 'volume_ratio', 'operator': '>', 'value': 1.5, 'lookback': 5}
        ],
        'narrative': '{currency_pair} breaking above key resistance at {resistance_level} on high volume',
        'priority': 'high',
        'asset_class': 'forex'
    },
    'volatility_expansion': {
        'conditions': [
            {'metric': 'atr_ratio', 'operator': '>', 'value': 1.5, 'lookback': 14},
            {'metric': 'volume_ratio', 'operator': '>', 'value': 1.3, 'lookback': 5}
        ],
        'narrative': '{currency_pair} experiencing volatility expansion with ATR at {atr}, suggesting potential breakout',
        'priority': 'high',
        'asset_class': 'forex'
    }
}

CRYPTO_RULES = {
    'bitcoin_dominance': {
        'conditions': [
            {'metric': 'btc_dominance', 'operator': '>', 'value': 45, 'lookback': 0},
            {'metric': 'altcoin_index_change', 'operator': '<', 'value': -2, 'lookback': 1}
        ],
        'narrative': 'Bitcoin dominance increasing at {btc_dominance}%, altcoins under pressure with {altcoin_index_change}% decline',
        'priority': 'medium',
        'asset_class': 'crypto'
    },
    'exchange_flows': {
        'conditions': [
            {'metric': 'exchange_inflows_ratio', 'operator': '>', 'value': 1.5, 'lookback': 7},
            {'metric': 'price_change_pct', 'operator': '<', 'value': -5, 'lookback': 7}
        ],
        'narrative': 'Increasing exchange inflows ({exchange_inflows_ratio}x average) suggest potential selling pressure for {crypto_asset}',
        'priority': 'medium',
        'asset_class': 'crypto'
    },
    'whale_activity': {
        'conditions': [
            {'metric': 'large_transaction_count', 'operator': '>', 'value': '1.8*average', 'lookback': 1},
            {'metric': 'transaction_value', 'operator': '>', 'value': '1000000', 'lookback': 0}
        ],
        'narrative': 'Elevated whale activity detected with {large_transaction_count} large transactions, potentially signaling market movement',
        'priority': 'high',
        'asset_class': 'crypto'
    },
    'defi_tvl_growth': {
        'conditions': [
            {'metric': 'tvl_growth_pct', 'operator': '>', 'value': 10, 'lookback': 30},
            {'metric': 'token_price_change', 'operator': '>', 'value': 15, 'lookback': 30}
        ],
        'narrative': 'Strong DeFi growth with TVL up {tvl_growth_pct}% in 30 days, driving {token_price_change}% price appreciation',
        'priority': 'medium',
        'asset_class': 'crypto'
    }
}

STOCK_RULES = {
    'earnings_impact': {
        'conditions': [
            {'metric': 'volume_ratio', 'operator': '>', 'value': 2, 'lookback': 1},
            {'metric': 'implied_volatility', 'operator': '>', 'value': 30, 'lookback': 0},
            {'news_keywords': ['earnings', 'results', 'quarterly'], 'min_articles': 1}
        ],
        'narrative': '{company} showing elevated volume ({volume_ratio}x average) and {implied_volatility}% IV ahead of earnings',
        'priority': 'high',
        'asset_class': 'stocks'
    },
    'sector_rotation': {
        'conditions': [
            {'metric': 'sector_performance', 'operator': '>', 'value': 3, 'lookback': 5},
            {'metric': 'relative_strength', 'operator': '>', 'value': 70, 'lookback': 0}
        ],
        'narrative': 'Sector rotation favoring {sector}, up {sector_performance}% in past week with RS of {relative_strength}',
        'priority': 'medium',
        'asset_class': 'stocks'
    },
    'insider_trading': {
        'conditions': [
            {'metric': 'insider_buy_ratio', 'operator': '>', 'value': 3, 'lookback': 30},
            {'metric': 'insider_transaction_volume', 'operator': '>', 'value': '2*average', 'lookback': 30}
        ],
        'narrative': 'Notable insider buying with {insider_buy_ratio}x more buys than sells, totaling {insider_transaction_volume} shares',
        'priority': 'medium',
        'asset_class': 'stocks'
    },
    'short_interest': {
        'conditions': [
            {'metric': 'short_interest_ratio', 'operator': '>', 'value': 20, 'lookback': 0},
            {'metric': 'borrowing_cost', 'operator': '>', 'value': 5, 'lookback': 0}
        ],
        'narrative': 'High short interest at {short_interest_ratio}% of float with {borrowing_cost}% borrow cost, potential squeeze setup',
        'priority': 'high',
        'asset_class': 'stocks'
    },
    'institutional_accumulation': {
        'conditions': [
            {'metric': 'institutional_net_flow', 'operator': '>', 'value': '10000000', 'lookback': 5},
            {'metric': 'block_trades', 'operator': '>', 'value': '1.5*average', 'lookback': 5}
        ],
        'narrative': 'Institutional accumulation detected with ${institutional_net_flow} net inflows and {block_trades} block trades',
        'priority': 'medium',
        'asset_class': 'stocks'
    }
}

# Combined rules dictionary
RULES_BY_ASSET_CLASS = {
    'forex': FOREX_RULES,
    'crypto': CRYPTO_RULES,
    'stocks': STOCK_RULES
}
