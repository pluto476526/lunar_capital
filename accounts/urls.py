## accounts/urls/py
## pkibuka@milky-way.space


from django.urls import path
from accounts import views


urlpatterns = [
    path("register/", views.signup_view, name="signup"),
    path("sign-in/", views.signin_view, name="signin"),
]
