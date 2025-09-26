## data_factory/news_processor.py
## pkibuka@milky-way.space

import logging

logger = logging.getLogger(__name__)

# Expanded keyword mapping
ASSET_KEYWORDS = {
    "forex": [
        "usd",
        "eur",
        "jpy",
        "gbp",
        "cny",
        "forex",
        "currency",
        "exchange rate",
        "foreign exchange",
        "yen",
        "euro",
        "pound",
        "dollar",
    ],
    "stocks": [
        "stock",
        "shares",
        "nasdaq",
        "dow jones",
        "s&p",
        "sp500",
        "equity",
        "ipo",
        "earnings",
        "guidance",
        "sector",
        "dividend",
        "index",
        "ftse",
        "dax",
        "nikkei",
        "russell 2000",
    ],
    "crypto": [
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "crypto",
        "cryptocurrency",
        "blockchain",
        "binance",
        "coinbase",
        "altcoin",
        "defi",
        "nft",
        "stablecoin",
        "token",
        "exchange",
        "wallet",
    ],
    "commodities": [
        "oil",
        "brent",
        "wti",
        "crude",
        "gas",
        "energy",
        "gold",
        "silver",
        "copper",
        "platinum",
        "commodity",
    ],
    "bonds": [
        "bond",
        "bonds",
        "treasury",
        "yield",
        "gilts",
        "fixed income",
        "sovereign debt",
        "corporate bond",
        "10-year",
        "30-year",
    ],
    "macro": [
        "inflation",
        "deflation",
        "recession",
        "economy",
        "growth",
        "gdp",
        "central bank",
        "fed",
        "federal reserve",
        "ecb",
        "boj",
        "interest rate",
        "monetary policy",
        "fiscal policy",
        "stimulus",
    ],
}


def categorize_news(news_data):
    """
    Categorize news headlines into asset classes using simple keyword matching.
    Returns a dict: { "forex": [...], "stocks": [...], "crypto": [...], ... }
    """
    f_news = {asset: [] for asset in ASSET_KEYWORDS.keys()}
    f_news["general"] = []

    if not news_data or "articles" not in news_data:
        logger.warning("No articles found in news data")
        return f_news

    for article in news_data["articles"]:
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        content = (article.get("content") or "").lower()
        combined_text = f"{title} {description} {content}"

        matched_assets = []
        for asset, keywords in ASSET_KEYWORDS.items():
            if any(keyword in combined_text for keyword in keywords):
                f_news[asset].append(article)
                matched_assets.append(asset)

        if not matched_assets:
            f_news["general"].append(article)

    return f_news
