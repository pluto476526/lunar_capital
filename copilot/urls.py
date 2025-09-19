## copilot/urls/py
## pkibuka@milky-way.space


from django.urls import path
from copilot import views


urlpatterns = [
    path("", views.copilot_view, name="copilot"),
    path("fx/", views.dash_fx_view, name="dash_fx"),
    path("crypto/", views.dash_crypto_view, name="dash_crypto"),
    path("stocks/", views.dash_stocks_view, name="dash_stocks"),
    path("fx/USD-JPY/", views.fx_details_view, name="fx_details"),
    path("crypto/<str:asset>/", views.crypto_details_view, name="crypto_details"),
    path("stock/MSFT/", views.stock_details_view, name="stock_details"),
    path("shenanigans/", views.fun_stuff_view, name="fun_stuff"),
    path("economic_calendar/", views.economic_calendar_view, name="calendar"),
    path("reddit/", views.reddit_feeds_view, name="reddit_feeds"),
    path("headlines/", views.all_news_view, name="all_news"),
    path("journal/", views.journal_view, name="journal"),
    path("test_strategy/", views.strategy_tester_view, name="strategy_tester"),
    path("plan_trade/", views.trade_planner_view, name="trade_planner"),
    path("performance/", views.performance_metrics_view, name="performance_metrics"),
    path("screener/", views.screener_view, name="screener"),
    path("repo/", views.repo_view, name="repo"),
]









