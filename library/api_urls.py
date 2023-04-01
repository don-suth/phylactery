from django.urls import path
from . import api_viewsets
app_name = 'library'

urlpatterns = [
	path('items/all', api_viewsets.ItemViewSet.as_view({'get': 'all_items'})),
	path('items/random/item', api_viewsets.ItemViewSet.as_view({'get': 'random_item'})),
	path('items/random/book', api_viewsets.ItemViewSet.as_view({'get': 'random_book'})),
	path('items/random/boardgame', api_viewsets.ItemViewSet.as_view({'get': 'random_boardgame'})),
	path('items/random/cardgame', api_viewsets.ItemViewSet.as_view({'get': 'random_cardgame'})),
]