from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from .models import Item, BorrowRecord
from .forms import ItemSelectForm, ItemDueDateForm, MemberBorrowDetailsForm
from django.http import HttpResponse, HttpResponseBadRequest
from django.forms import formset_factory
from django.views import generic
from dal import autocomplete
from taggit.models import Tag
from django.db.models import Q
from django.contrib import messages
from members.decorators import gatekeeper_required
import datetime
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
        today = datetime.date.today()
        tomorrow = today+datetime.timedelta(days=1)
        context['today'] = True if today == context['item_info']['expected_availability_date'] else False
        context['tomorrow'] = True if tomorrow == context['item_info']['expected_availability_date'] else False

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
        qs = Item.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class SearchView(generic.ListView):
    template_name = 'library/item_list_view.html'
    context_object_name = 'items_list'
    model = Item
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        if not q:
            return redirect('library:library-home')
        vector = \
            SearchVector('name', weight='A') + \
            SearchVector('description', weight='B') + \
            SearchVector('base_tags__base_tags__name', weight='B') + \
            SearchVector('computed_tags__computed_tags__name', weight='B')
        search_query = SearchQuery(q)
        qs = Item.objects \
            .annotate(rank=SearchRank(vector, search_query, weights=[0.5, 0.7, 0.9, 1.0])) \
            .filter(rank__gte=0.2) \
            .order_by('pk', 'rank') \
            .distinct('pk')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Results for the search '{0}'".format(self.request.GET.get('q',''))
        return context


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
        qs = Item.objects.filter(is_borrowable=True)
    items_list = qs.order_by('name')[(page-1)*10:(page*10)-1]
    return render(request, 'library/item_list_view.html', {'items_list': items_list})


@gatekeeper_required
def borrow_view(request):
    form = ItemSelectForm
    return render(request, 'library/borrow_form.html', {'form': form})


@gatekeeper_required
def borrow_view_2(request):
    if request.method == 'POST':
        received_form = ItemSelectForm(request.POST)
        if received_form.is_valid():
            item_formset = formset_factory(ItemDueDateForm, extra=0)
            formset_data = []
            rejected_items = []
            differing_due_date = []
            for item in received_form.cleaned_data['items']:
                # Make a new form for each item
                item_info = item.get_availability_info()
                if not item_info['is_available']:
                    rejected_items.append(item.name)
                else:
                    if item_info['max_due_date'] != datetime.date.today()+datetime.timedelta(weeks=2):
                        # A due date different than usual is among us. Make sure the gatekeeper knows.
                        differing_due_date.append(True)
                    else:
                        differing_due_date.append(False)
                    formset_data.append({'item': item, 'due_date': item_info['max_due_date']})
            if True in differing_due_date:
                messages.warning(
                    request,
                    'Note: One or more items below has a due date earlier than two weeks from now. '
                    'Make sure that this due date still suits the borrower.'
                )
            if rejected_items and formset_data:
                messages.error(
                    request,
                    'The following items are not available at the moment, and are thus not included: '
                    + ', '.join(rejected_items)
                    + '. Is you believe this to be an error, contact the Librarian.'
                )
                formset = item_formset(initial=formset_data)
                borrow_form = MemberBorrowDetailsForm()
                return render(
                    request, 'library/borrow_form_2.html',
                    {'formset': formset, 'borrow_form': borrow_form, 'diff': differing_due_date}
                )
            elif rejected_items and not formset_data:
                messages.error(
                    request,
                    "All items you selected are not available, and can't be borrowed. "
                    "If you believe this to be an error, contact the Librarian."
                )
                return redirect('library:borrow')
            elif formset_data:
                formset = item_formset(initial=formset_data)
                borrow_form = MemberBorrowDetailsForm()
                return render(
                    request, 'library/borrow_form_2.html',
                    {'formset': formset, 'borrow_form': borrow_form, 'diff': differing_due_date}
                )
            else:
                return redirect('library:borrow')
        else:
            return render(request, 'library/borrow_form.html', {'form': received_form})
    else:
        return redirect('library:borrow')


@gatekeeper_required
def borrow_view_3(request):
    item_formset = formset_factory(ItemDueDateForm)
    if request.method == 'POST':
        borrow_form = MemberBorrowDetailsForm(request.POST)
        formset = item_formset(request.POST)
        if formset.is_valid() and borrow_form.is_valid():
            context = {'items': []}
            borrowing_member = borrow_form.cleaned_data['member']
            member_address = borrow_form.cleaned_data['address']
            member_phone_number = borrow_form.cleaned_data['phone_number']
            auth_gatekeeper_borrow = request.user.member
            for form in formset:
                item = form.cleaned_data['item']
                due_date = form.cleaned_data['due_date']
                # Create a new borrowing entry for each item
                BorrowRecord.objects.create(
                    borrowing_member=borrowing_member,
                    member_address=member_address,
                    member_phone_number=member_phone_number,
                    auth_gatekeeper_borrow=auth_gatekeeper_borrow,
                    item=item,
                    due_date=due_date,
                )
                context['items'].append([str(item), str(due_date)])
            context['member'] = str(borrowing_member)
            context['address'] = str(member_address)
            context['phone_number'] = str(member_phone_number)
            context['gatekeeper'] = str(auth_gatekeeper_borrow)
            return render(request, 'library/borrow_form_success.html', context)
        else:
            return render(request, 'library/borrow_form_2.html', {'formset': formset, 'borrow_form': borrow_form})
    else:
        return redirect('library:borrow')
