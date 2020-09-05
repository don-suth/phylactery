from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

app_name = 'library'
urlpatterns = [
    path('item/<int:item_id>/', views.item_detail, name='detail-id'),
    path('item/<slug:slug>/', views.item_detail, name='detail-slug'),
    path('', views.item_list, name='items-all')
]