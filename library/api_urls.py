from django.urls import path
from . import api_viewsets
app_name = 'library'

urlpatterns = [
	#path('all', api_viewsets.ItemViewSet.as_view({'get': 'all_items'})),
	path('random/any', api_viewsets.ItemViewSet.as_view({'get': 'random_item'})),
	path('random/book', api_viewsets.ItemViewSet.as_view({'get': 'random_book'})),
	path('random/boardgame', api_viewsets.ItemViewSet.as_view({'get': 'random_boardgame'})),
	path('random/cardgame', api_viewsets.ItemViewSet.as_view({'get': 'random_cardgame'})),
]