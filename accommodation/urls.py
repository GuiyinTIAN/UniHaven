from django.urls import path
from . import views

urlpatterns = [
    path("lookup-address/", views.lookup_address, name="lookup_address"),
    path("add-accommodation/", views.add_accommodation, name="add_accommodation"),
]

urlpatterns += [
    path("list-accommodation/", views.accommodation_list, name="accommodation_list"),
]
