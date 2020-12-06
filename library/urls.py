from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views
from dal import autocomplete
from taggit.models import Tag

app_name = 'library'
urlpatterns = [
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='detail-id'),
    path('tag/strtag/<int:pk>/', views.AllItemsByStrTag.as_view(), name='strtag-all'),
    # path('item/<slug:slug>/', views.item_detail, name='detail-slug'),
    path('autostrtag/', views.StrTagValueAutocomplete.as_view(), name='strtagvalue-autocomplete'),
    path(
        'test-autocomplete/',
        views.TagAutocomplete.as_view(create_field=None),
        name='select2_taggit',
    ),
    path('', views.AllItemsView.as_view(), name='items-all'),
]
