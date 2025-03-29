from django.urls import path
from . import views

urlpatterns = [
    path("lookup-address/", views.lookup_address, name="lookup_address"),
    path("add-accommodation/", views.add_accommodation, name="add_accommodation"),
    path("list-accommodation/", views.list_accommodation, name="list_accommodation"),
]
