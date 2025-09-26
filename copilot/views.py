## copilot/views.py
## pkibuka@milky-way.space

from data_factory.performance_metrics import TradingPerformanceAnalyzer as TPA
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse
import logging, os, time
import pandas as pd


logger = logging.getLogger(__name__)

def get_report_id():
    return int(time.time())


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
    context = {
        "report_id": get_report_id(),
        "total_trades": None,
        "total_buys": None,
        "total_sells": None,
        "total_volume": None,
        "total_trade_value": None,
        "win_rate": None,
        "avg_win": None,
        "avg_loss": None,
        "largest_win": None,
        "largest_loss": None,
        "profit_factor": None,
        "expectancy": None,
        "sharpe_ratio": None,
        "max_drawdown": None,
        "val_at_risk": None,
        "avg_win_loss": None,
        "symbols": None,
    }

    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        initial_capital = request.POST.get("initial_capital")
        base_currency = request.POST.get("base_currency") or "GBP"

        if not csv_file:
            return render(request, "copilot/performance_metrics.html", context)

        try:
            initial_capital = float(initial_capital)
        except Exception:
            initial_capital = 10000.0

        try:
            # Process the CSV file
            analyzer = TPA(csv=csv_file, initial_capital=initial_capital, base_currency=base_currency)
            report = analyzer.generate_report()
            cache.set(context["report_id"], report, 3600)
            request.session["report_id"] = context["report_id"]

            # Extract metrics
            context["total_trades"] = report['Summary']['Total Trades']
            context["total_buys"] = report['Summary']['Total Buys']
            context["total_sells"] = report['Summary']['Total Sells']
            context["total_volume"] = report['Summary']['Total Volume']
            context["win_rate"] = report['Performance']['Win Rate %']
            context["total_trade_value"] = round(float(report['Summary']['Total Trade Value (Base)']), 2)
            context["avg_win"] = round(float(report['Performance']['Average Win (Base)']), 2)
            context["avg_loss"] = round(abs(float(report['Performance']['Average Loss (Base)'])), 2)
            context["largest_win"] = round(float(report['Performance']['Largest Win (Base)']), 2)
            context["largest_loss"] = round(float(report['Performance']['Largest Loss (Base)']), 2)
            context["profit_factor"] = round(float(report['Performance']['Profit Factor']), 2)
            context["expectancy"] = round(float(report['Performance']['Expectancy (Base)']), 2)
            context["sharpe_ratio"] = round(float(report['Performance']['Sharpe Ratio']), 2)
            context["max_drawdown"] = round(float(report['Risk']['Max Drawdown']), 2)
            context["val_at_risk"] = round(float(report['Risk']['Value at Risk (95%) (Base)']), 2)
            context["symbols"] = report['Symbols']

            # Calculate Avg Win/Loss ratio
            context["avg_win_loss"] = round(context["avg_win"] / context["avg_loss"], 2) if context["avg_loss"] != 0 else "N/A"

        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")

    return render(request, "copilot/performance_metrics.html", context)


def download_report_view(request, file_type):
    report_id = request.session.get("report_id")
    if not report_id:
        return HttpResponse("No report found in session.", status=400)

    report_data = cache.get(report_id)
    if not report_data:
        return HttpResponse("Report expired or missing in cache.", status=400)

    analyzer = TPA(report_data=report_data)

    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = os.path.join(reports_dir, f"{report_id}.{file_type}")

    try:
        analyzer.export_report(filename, file_type)
        with open(filename, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = f"attachment; filename=performance_metrics.{file_type}"
            return response
    except Exception as e:
        logger.error(f"Error generating download file: {e}", exc_info=True)
        return HttpResponse(f"Error generating file: {e}", status=500)


def screener_view(request):
    context = {}
    return render(request, "copilot/screener.html", context)

def repo_view(request):
    context = {}
    return render(request, "copilot/repo.html", context)






















