## copilot/views.py
## pkibuka@milky-way.space

from django.shortcuts import render


def copilot_view(request):
    context = {}
    return render(request, "copilot/index.html", context)


def advanced_overview(request):
    context = {}
    return render(request, "copilot/advanced_overview.html", context)
