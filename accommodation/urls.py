from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"), 
    path("lookup-address/", views.lookup_address, name="lookup_address"),
    path("add-accommodation/", views.add_accommodation, name="add_accommodation"),
    path("list-accommodation/", views.list_accommodation, name="list_accommodation"),
    path("search-accommodation/", views.search_accommodation, name="search_accommodation"),
    path("accommodation_detail/<int:id>/", views.accommodation_detail, name="accommodation_detail"),
    path("reserve_accommodation/", views.reserve_accommodation, name="reserve_accommodation"),
    path("cancel_reservation/", views.cancel_reservation, name="cancel_reservation"),
    path("delete-accommodation/", views.delete_accommodation, name="delete_accommodation"),
    path('rate/<int:accommodation_id>/', views.rate_accommodation, name='rate_accommodation'),  
]
