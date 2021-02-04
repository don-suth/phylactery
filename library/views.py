from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from .models import Item, BorrowRecord, ExternalBorrowingRecord
from .forms import ItemSelectForm, ItemDueDateForm, MemberBorrowDetailsForm, VerifyReturnForm, ReturnItemsForm
from members.models import Member
from django.http import HttpResponse, HttpResponseBadRequest
from django.forms import formset_factory
from django.views import generic
from dal import autocomplete
from taggit.models import Tag
from django.db.models import Q, Count
from django.contrib import messages
from members.decorators import gatekeeper_required
import datetime
from django.core.exceptions import ObjectDoesNotExist
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
        context['page_title'] = "Results for the search '{0}'".format(self.request.GET.get('q', ''))
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


@gatekeeper_required
def overview_view(request):
    today = datetime.date.today()
    three_weeks_ago = today - datetime.timedelta(weeks=3)
    context = {
        'today': today,
        'currently_borrowed': BorrowRecord.objects.filter(date_returned=None).order_by('due_date'),
        'needing_return_verification': BorrowRecord.objects.exclude(date_returned=None).exclude(verified_returned=True),
        'unapproved_borrow_requests': ExternalBorrowingRecord.objects.filter(due_date=None),
        'approved_borrow_requests': ExternalBorrowingRecord.objects.exclude(due_date=None).filter(date_returned=None),
        'members_borrowing': Member.objects.annotate(
            num_borrowed=Count('borrowed', filter=Q(borrowed__date_returned=None))
            ).filter(
                num_borrowed__gt=0
        ),
        'overdue': BorrowRecord.objects.filter(date_returned=None, due_date__lt=today).order_by('due_date'),
        'recent_records': BorrowRecord.objects.filter(date_borrowed__gte=three_weeks_ago).order_by('date_borrowed')
    }
    errors = False
    if request.method == 'POST':
        form_type = request.POST.get('form_type', None)
        form = None
        if form_type == 'return_items':
            form = VerifyReturnForm(request.POST)
            if form.is_valid():
                validated = []
                for field_name in form.cleaned_data.keys():
                    if form.cleaned_data[field_name] is True:
                        try:
                            pk = field_name.split('return_')[1]
                            record = BorrowRecord.objects.get(pk=pk)
                        except (IndexError, ObjectDoesNotExist) as e:
                            errors = True
                            continue
                        if record.verified_returned is False and record.date_returned is not None:
                            record.verified_returned = True
                            record.save()
                            validated.append(pk)
                if validated:
                    messages.success(
                        request,
                        "Successfully verified {0} item{1} as returned."
                            .format(len(validated), 's' if len(validated) > 1 else '')
                    )
    if errors:
        messages.error(
            request,
            'There were one or more errors with your request. Please try again.'
            'If you repeatedly get this error, please contact a WebKeeper.'
        )
    return render(request, 'library/overview.html', context)


@gatekeeper_required
def return_item_view(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'GET':
        form = ReturnItemsForm(member_pk=pk)
        if form.qs.exists():
            context = {
                'member': member,
                'borrowed_items': form.qs,
            }
            return render(request, template_name='library/return_member_items.html', context=context)
        else:
            messages.error(request, 'This member has no items to return.')
            return redirect('members:profile', pk=pk)
    elif request.method == 'POST':
        form = ReturnItemsForm(request.POST, member_pk=pk)
        context = {
            'member': member,
            'borrowed_items': form.qs,
        }
        if form.is_valid():
            successfully_returned = []
            errors = False
            today = datetime.date.today()
            for field in form.cleaned_data:
                if form.cleaned_data[field] is True:
                    try:
                        record_pk = field.split('return_')[1]
                        record = BorrowRecord.objects.get(pk=int(record_pk), borrowing_member=member)
                    except (IndexError, ObjectDoesNotExist):
                        print('errors')
                        errors = True
                        continue
                    record.date_returned = today
                    record.auth_gatekeeper_return = request.user.member
                    record.save()
                    successfully_returned.append(record_pk)
            if successfully_returned:
                messages.success(
                    request,
                    "Successfully returned {0} item{1}."
                        .format(len(successfully_returned), 's' if len(successfully_returned) > 1 else '')
                )
            if errors:
                messages.error(
                    request,
                    'There were one or more errors with your request. Please try again.'
                    'If you repeatedly get this error, please contact a WebKeeper.'
                )
                context['borrowed_items'] = context['borrowed_items'].all()
                return render(request, template_name='library/return_member_items.html', context=context)
            return redirect('members:profile', pk=pk)
        else:
            return render(request, template_name='library/return_member_items.html', context=context)
