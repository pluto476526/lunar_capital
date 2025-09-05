# data_factory/rules_config.py
FOREX_RULES = {
    'central_bank_impact': {
        'conditions': [
            {'metric': 'price', 'operator': '>', 'value': '2%', 'lookback': 1},
            {'news_keywords': ['central bank', 'interest rates', 'policy'], 'min_articles': 2}
        ],
        'narrative': '{currency} reacting to {central_bank} policy expectations',
        'priority': 'high',
        'asset_class': 'forex'
    }
}

CRYPTO_RULES = {
    'bitcoin_dominance': {
        'conditions': [
            {'metric': 'btc_dominance', 'operator': '>', 'value': 45, 'lookback': 0},
            {'metric': 'altcoin_index', 'operator': '<', 'value': '2%', 'lookback': 1}
        ],
        'narrative': 'Bitcoin dominance increasing at {btc_dominance}%, altcoins under pressure',
        'priority': 'medium',
        'asset_class': 'crypto'
    },
    'exchange_flows': {
        'conditions': [
            {'metric': 'exchange_inflows', 'operator': '>', 'value': '1.5*average', 'lookback': 7},
            {'metric': 'price', 'operator': '<', 'value': '5%', 'lookback': 7}
        ],
        'narrative': 'Increasing exchange inflows suggest potential selling pressure',
        'priority': 'medium',
        'asset_class': 'crypto'
    }
}

STOCK_RULES = {
    'earnings_impact': {
        'conditions': [
            {'metric': 'volume', 'operator': '>', 'value': '2*average', 'lookback': 1},
            {'metric': 'implied_volatility', 'operator': '>', 'value': '30%', 'lookback': 0},
            {'news_keywords': ['earnings', 'results', 'quarterly'], 'min_articles': 1}
        ],
        'narrative': '{company} showing elevated volume and volatility ahead of earnings',
        'priority': 'high',
        'asset_class': 'stocks'
    },
    'sector_rotation': {
        'conditions': [
            {'metric': 'sector_performance', 'operator': '>', 'value': '3%', 'lookback': 5},
            {'metric': 'relative_strength', 'operator': '>', 'value': 70, 'lookback': 0}
        ],
        'narrative': 'Sector rotation favoring {sector}, up {performance}% in past week',
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
