## copilot/urls/py
## pkibuka@milky-way.space


from django.urls import path
from copilot import views


urlpatterns = [
    path("", views.copilot_view, name="copilot"),
    path("advanced_overview/", views.advanced_overview, name="advanced_overview"),
]
