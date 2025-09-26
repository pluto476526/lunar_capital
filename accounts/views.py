## accounts/views.py
## pkibuka@milky-way.space

import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


def signup_view(request):
    context = {}
    return render(request, "accounts/sign_up.html", context)


def signin_view(request):
    context = {}
    return render(request, "accounts/sign_in.html", context)
