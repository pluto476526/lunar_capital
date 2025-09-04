## home/views.py
## pkibuka@milky-way.space

from django.shortcuts import render

def home_view(request):
    context = {}
    return render(request, "home/main.html", context)
