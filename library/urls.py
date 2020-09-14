from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

app_name = 'library'
urlpatterns = [
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='detail-id'),
    # path('item/<slug:slug>/', views.item_detail, name='detail-slug'),
    path('', views.IndexView.as_view(), name='items-all')
]