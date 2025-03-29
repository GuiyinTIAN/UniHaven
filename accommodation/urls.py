from django.urls import path
from . import views

urlpatterns = [
    path("lookup-address/", views.lookup_address, name="lookup_address"),
]
