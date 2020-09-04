from django.shortcuts import render, get_object_or_404, redirect
from .models import Item


# Create your views here.
def item_detail(request, item_id=None, slug=None):
    if item_id is not None:
        item = get_object_or_404(Item, pk=item_id)
        return redirect(item)
    elif slug is not None:
        item = get_object_or_404(Item, item_slug=slug)
    return render(request, 'library/item_view.html', {'item': item})
