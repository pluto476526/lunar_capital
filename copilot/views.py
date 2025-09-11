## copilot/views.py
## pkibuka@milky-way.space

from django.shortcuts import render
from data_factory import engine, tasks
import logging


def copilot_view(request):
    context = {}
    return render(request, "copilot/copilot.html", context)


def dash_fx_view(request):
    """
    Get FX market overview
    """
    # result = tasks.fetch_and_process_forex_data.delay().get(timeout=30)
    # market_data, _ = result if isinstance(result, tuple) else (result, None)
    # context = {
    #     "fx_data": market_data,
    # }
    context = {}
    return render(request, "copilot/dash_fx.html", context)


def dash_crypto_view(request):
    context = {}
    return render(request, "copilot/dash_crypto.html", context)


def dash_stocks_view(request):
    context = {}
    return render(request, "copilot/dash_stocks.html", context)

def fx_details_view(request, symbol):
    """
    Get detailed info for a specific currency pair
    """
    # result = tasks.fetch_and_process_forex_data.delay(single_symbol=symbol).get(timeout=30)
    # _, symbol_data = result if isinstance(result, tuple) else (None, result)
    # context = {
    #     "fx_details": symbol_data,
    # }
    context = {}
    return render(request, "copilot/fx_details.html", context)

def crypto_details_view(request):
    context = {}
    return render(request, "copilot/crypto_details.html", context)

def stock_details_view(request):
    context = {}
    return render(request, "copilot/stock_details.html", context)

def fun_stuff_view(request):
    context = {}
    return render(request, "copilot/fun.html", context)

def economic_calendar_view(request):
    context = {}
    return render(request, "copilot/economic_calendar.html", context)

def reddit_feeds_view(request):
    context = {}
    return render(request, "copilot/reddit_feeds.html", context)

def all_news_view(request):
    context = {}
    return render(request, "copilot/all_news.html", context)

def journal_view(request):
    context = {}
    return render(request, "copilot/journal.html", context)

def strategy_tester_view(request):
    context = {}
    return render(request, "copilot/strategy_tester.html", context)

def trade_planner_view(request):
    context = {}
    return render(request, "copilot/trade_planner.html", context)

def performance_metrics_view(request):
    context = {}
    return render(request, "copilot/performance_metrics.html", context)

def screener_view(request):
    context = {}
    return render(request, "copilot/screener.html", context)

def repo_view(request):
    context = {}
    return render(request, "copilot/repo.html", context)






















