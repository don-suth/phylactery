from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
    path('<int:item_id>/', views.item_detail, name='detail')
]