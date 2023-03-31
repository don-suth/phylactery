from django.urls import path
from . import views
app_name = 'library'

urlpatterns = [
	path('items/all', views.item_list_api)
]