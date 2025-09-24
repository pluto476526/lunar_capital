## copilot/views.py
## pkibuka@milky-way.space

from data_factory.performance_metrics import TradingPerformanceAnalyzer as TPA
from django.shortcuts import render
import pandas as pd
import logging


logger = logging.getLogger(__name__)

def copilot_view(request):
    context = {}
    return render(request, "copilot/copilot.html", context)


def dash_fx_view(request):
    """
    Get FX market overview
    """
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
    context = {}
    return render(request, "copilot/fx_details.html", context)

def crypto_details_view(request, symbol):
    context = {}
    return render(request, "copilot/crypto_details.html", context)

def stock_details_view(request, symbol):
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
    report = None
    error = None

    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        initial_capital = request.POST.get("initial_capital")
        base_currency = request.POST.get("base_currency") or "GBP"

        try:
            initial_capital = float(initial_capital)
        except ValueError:
            initial_capital = 10000

        if csv_file:
            try:
                # Process the data
                analyzer = TPA(csv_file, initial_capital, base_currency)
                report = analyzer.generate_report()
                    
            except Exception as e:
                error = f"Error processing CSV file: {str(e)}"

    context = {"report": report, "error": error}
    logger.debug(f"Performance metrics context: {context}")
    return render(request, "copilot/performance_metrics.html", context)

def screener_view(request):
    context = {}
    return render(request, "copilot/screener.html", context)

def repo_view(request):
    context = {}
    return render(request, "copilot/repo.html", context)






















