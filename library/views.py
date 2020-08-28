from django.shortcuts import render, get_object_or_404
from .models import Item


# Create your views here.
def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    return render(request, 'library/item_view.html', {'item': item})
