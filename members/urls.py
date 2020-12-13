from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
	path('signup/', views.signup, name='signup'),
	path('activate/<uidb64>/<token>/', views.activate, name='activate'),
]
