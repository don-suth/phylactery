from django.shortcuts import render, get_object_or_404, redirect
from .models import Item
from .forms import ItemSelectForm
from django.http import HttpResponseBadRequest
from django.views import generic
from dal import autocomplete
from taggit.models import Tag
from django.db.models import Q
# Create your views here.


class AllItemsView(generic.ListView):
    template_name = 'library/item_list_view.html'
    context_object_name = 'items_list'
    model = Item
    paginate_by = 20


class AllItemsByTag(generic.ListView):
    template_name = 'library/item_list_view.html'
    context_object_name = 'items_list'
    model = Item
    paginate_by = 20


    def get_queryset(self):
        self.tag_name = get_object_or_404(Tag, pk=self.kwargs['pk']).name
        return Item.objects.filter(
            Q(base_tags__base_tags__name__in=[self.tag_name]) |
            Q(computed_tags__computed_tags__name__in=[self.tag_name])) \
            .distinct() \
            .order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "All items with the tag {0}".format(self.tag_name)
        return context


class ItemDetailView(generic.DetailView):
    model = Item
    template_name = 'library/item_detail_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_info'] = self.object.get_availability_info()
        return context


class TagAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Tag.objects.none()

        qs = Tag.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class LibraryItemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # We don't care if the user is authenticated here
        qs = Item.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


def item_detail(request, item_id=None, slug=None):
    if item_id is not None:
        item = get_object_or_404(Item, pk=item_id)
        return redirect(item)
    elif slug is not None:
        item = get_object_or_404(Item, slug=slug)
    else:
        return HttpResponseBadRequest("Invalid request")
    return render(request, 'library/item_detail_view.html', {'item': item})


def item_list(request, page=1, qs=None):
    # Shows a list of all items, sorted alphabetically, in pages of 10
    # 0-9, 10-19, etc.
    if not qs:
        qs = Item.objects.all()
    items_list = qs.order_by('name')[(page-1)*10:(page*10)-1]
    return render(request, 'library/item_list_view.html', {'items_list': items_list})


def borrow_view(request):
    form = ItemSelectForm
    return render(request, 'library/borrow_form.html', {'form': form})
