## home/urls/py
## pkibuka@milky-way.space


from django.urls import path
from home import views


urlpatterns = [
    path("", views.home_view, name="home"),
    ## path("notifications/", views.notifications_view, name="notifications"),
    ## path("faqs/", views.faqs_view, name="faqs")
]
