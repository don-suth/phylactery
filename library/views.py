from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from .models import Item, BorrowRecord, ExternalBorrowingForm, TagParent, \
    BOOK, BOARD_GAME, CARD_GAME, OTHER
from members.models import switch_to_proxy
from .forms import ItemSelectForm, ItemDueDateForm, MemberBorrowDetailsForm, VerifyReturnForm, ReturnItemsForm, \
    ExternalBorrowingRequestForm, ExternalBorrowingLibrarianForm, ExternalBorrowingReturningForm
from members.models import Member
from django.http import HttpResponse, HttpResponseBadRequest
from django.forms import formset_factory
from django.views import generic
from dal import autocomplete
from taggit.models import Tag
from django.db.models import F, Q, Count
from django.contrib import messages
from members.decorators import gatekeeper_required
import datetime
from django.core.exceptions import ObjectDoesNotExist
from phylactery.tasks import compose_html_email, send_single_email_task
# Create your views here.


class LibraryHomeView(generic.ListView):
    template_name = 'library/home_view.html'
    context_object_name = 'items_list'
    model = Item
    featured_tag_name = 'Featured'

    def get_queryset(self):
        return Item.objects.filter(
            Q(base_tags__base_tags__name__in=[self.featured_tag_name])
        ).distinct().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['number_of_books'] = Item.objects.filter(type=BOOK).count()
        context['number_of_cardgames'] = Item.objects.filter(type=CARD_GAME).count()
        context['number_of_boardgames'] = Item.objects.filter(type=BOARD_GAME).count()
        context['number_of_other'] = Item.objects.filter(type=OTHER).count()
        return context


class AllTagsView(generic.ListView):
    template_name = 'library/tag_list_view.html'
    context_object_name = 'tags_list'
    model = Tag

    def get_queryset(self):
        qs = Tag.objects.all() \
            .exclude(name__startswith="Item: ") \
            .annotate(num_items=Count('itemcomputedtags')) \
            .order_by('-num_items', 'name')
        return qs


class AllItemsView(generic.ListView):
    template_name = 'library/item_list_view.html'
    context_object_name = 'items_list'
    model = Item
    paginate_by = 24


class AllItemsByTag(generic.ListView):
    template_name = 'library/item_list_view.html'
    context_object_name = 'items_list'
    model = Item
    paginate_by = 24

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, pk=self.kwargs['pk'])

        return Item.objects.filter(
            Q(base_tags__base_tags__name__in=[self.tag.name]) |
            Q(computed_tags__computed_tags__name__in=[self.tag.name])) \
            .distinct() \
            .order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "All items with the tag {0}".format(self.tag.name)
        context['parent_tags'] = Tag.objects.filter(children__child_tag=self.tag).exclude(name__startswith="Item:")
        context['child_tags'] = Tag.objects.filter(parents__parent_tag=self.tag).exclude(name__startswith="Item:")

        return context


class ItemDetailView(generic.DetailView):
    model = Item
    template_name = 'library/item_detail_view.html'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_info'] = self.object.get_availability_info()
        today = datetime.date.today()
        tomorrow = today+datetime.timedelta(days=1)
        context['today'] = (today == context['item_info']['expected_availability_date'])
        context['tomorrow'] = (tomorrow == context['item_info']['expected_availability_date'])
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
    paginate_by = 24

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
    form = ItemSelectForm()
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
                context['items'].append([str(item), due_date])
            context['member'] = borrowing_member
            context['address'] = str(member_address)
            context['phone_number'] = str(member_phone_number)
            context['gatekeeper'] = str(auth_gatekeeper_borrow)
            context['today'] = datetime.date.today()
            subject = "Unigames Borrow Receipt"
            message, html_message = compose_html_email('library/email_borrow_receipt.html', context)
            send_single_email_task.delay(
                borrowing_member.email_address,
                subject,
                message,
                html_message=html_message
            )
            return render(request, 'library/borrow_form_success.html', context)
        else:
            return render(request, 'library/borrow_form_2.html', {'formset': formset, 'borrow_form': borrow_form})
    else:
        return redirect('library:borrow')


@gatekeeper_required
def overview_view(request):
    today = datetime.date.today()
    three_weeks_ago = today - datetime.timedelta(weeks=3)
    external_forms = ExternalBorrowingForm.objects\
        .annotate(
            total_items=Count(
                'requested_items',
                distinct=True,
            ),
            borrowed_items=Count(
                'requested_items',
                filter=Q(
                    requested_items__date_borrowed__isnull=False,
                ),
                distinct=True,
            ),
            returned_items=Count(
                'requested_items',
                filter=Q(
                    requested_items__date_borrowed__isnull=False,
                    requested_items__date_returned__isnull=False,
                ),
                distinct=True,
            ),
        )
    context = {
        'today': today,
        'currently_borrowed': BorrowRecord.objects.filter(date_returned=None).order_by('due_date'),
        'needing_return': BorrowRecord.objects.exclude(date_returned=None).exclude(verified_returned=True),
        'unapproved_borrow_requests': external_forms.filter(
            form_status=ExternalBorrowingForm.UNAPPROVED
        ),
        'approved_borrow_requests': external_forms.filter(
            form_status=ExternalBorrowingForm.APPROVED,
        ).exclude(
            total_items=F('returned_items')
        ),
        'completed_borrow_requests': external_forms.filter(
            Q(form_status=ExternalBorrowingForm.DENIED)
            | Q(form_status=ExternalBorrowingForm.COMPLETED)
            | Q(form_status=ExternalBorrowingForm.APPROVED, total_items=F('returned_items'))
        ),
        'members_borrowing': Member.objects.annotate(
            num_borrowed=Count('borrowed', filter=Q(borrowed__date_returned=None))
            ).filter(
                num_borrowed__gt=0
        ),
        'overdue': BorrowRecord.objects.filter(date_returned=None, due_date__lt=today).order_by('due_date'),
        'recent_records': BorrowRecord.objects.filter(date_borrowed__gte=three_weeks_ago).order_by('date_borrowed')
    }
    u = switch_to_proxy(request.user)
    errors = False
    if request.method == 'POST' and u.is_committee:
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


def external_borrow_request_view(request):
    if request.method == 'GET':
        form = ExternalBorrowingRequestForm()
        return render(request, 'library/external_borrow_form.html', {'form': form})
    elif request.method == 'POST':
        form = ExternalBorrowingRequestForm(request.POST)
        if form.is_valid():
            form.submit()
            messages.success(request, 'Your form was successfully submitted! We will get in touch soon.')
            return redirect('library:library-home')
        else:
            return render(request, 'library/external_borrow_form.html', {'form': form})


@gatekeeper_required
def external_borrow_form_view(request, pk):
    VALID_GROUPS = ['Librarian', 'Vice-President', 'President', 'Admin']
    user_has_permissions = request.user.groups.filter(name__in=VALID_GROUPS).exists()
    external_borrow_form = get_object_or_404(ExternalBorrowingForm, pk=pk)
    today = datetime.date.today()
    item_data = []
    control_form = None
    all_borrow = True
    all_return = True
    any_borrow = False
    any_return = False
    for item_record in external_borrow_form.requested_items.all():
        status = 'Not Borrowable'
        actions = ''
        details = ''
        if external_borrow_form.form_status in (ExternalBorrowingForm.UNAPPROVED, ExternalBorrowingForm.DENIED):
            item_data.append((item_record, status, actions, details))
            continue
        if item_record.date_borrowed is None:
            # Item is not borrowed yet
            if today == external_borrow_form.requested_borrow_date:
                # Item is borrowable
                status = 'Awaiting Pickup'
                actions = 'b'
                all_return = False
                any_borrow = True
        elif item_record.date_returned is None:
            # Item has been borrowed and not returned
            actions = 'r'
            all_borrow = False
            any_return = True
            details = 'Borrowed by {0} on {1}. Authorised by {2}.'.format(
                item_record.borrower_name,
                str(item_record.date_borrowed),
                str(item_record.auth_gatekeeper_borrow)
            )
            if today > external_borrow_form.due_date:
                # The item is overdue
                status = 'Borrowed & Awaiting Return (Overdue)'
            else:
                status = 'Borrowed & Awaiting Return'
        else:
            # Item has been borrowed and returned.
            details = \
                'Borrowed by {0} on {1}. Authorised by {2}.\n' \
                'Returned by {3} on {4}. Authorised by {5}' \
                    .format(
                        item_record.borrower_name,
                        str(item_record.date_borrowed),
                        str(item_record.auth_gatekeeper_borrow),
                        item_record.returner_name,
                        str(item_record.date_returned),
                        str(item_record.auth_gatekeeper_return)
                )
            status = 'Returned'
        item_data.append((item_record, status, actions, details))

    context = {
        'form_data': external_borrow_form,
        'item_data': item_data,
        'form': control_form,
        'show_control': user_has_permissions,
        'all_borrow': all_borrow and any_borrow,
        'all_return': all_return and any_return,
        'any_actions': any_borrow or any_return
    }

    if request.method == 'POST':
        form_name = request.POST.get('form-name', None)
        print(form_name)
        if request.POST.get('form-name', None) == 'librarian-control':
            if user_has_permissions:
                control_form = ExternalBorrowingLibrarianForm(request.POST, display_form=external_borrow_form)
                if control_form.is_valid():
                    # Form is valid, user has correct permissions
                    external_borrow_form.librarian_comments = control_form.cleaned_data['librarian_comments']
                    external_borrow_form.form_status = control_form.cleaned_data['form_status']
                    external_borrow_form.due_date = control_form.cleaned_data['due_date']
                    external_borrow_form.save()
                else:
                    context['form'] = control_form
                    return render(request, 'library/external_form_view.html', context)
            else:
                messages.error(request, "You don't have permission to do that.")
        if request.POST.get('form-name', None) == 'borrow-return':
            submitted_form = ExternalBorrowingReturningForm(
                request.POST, submitted_form=external_borrow_form, auth_gatekeeper=request.user.member)
            if submitted_form.is_valid() and external_borrow_form.due_date is not None:
                borrowed, returned = submitted_form.submit()
                if borrowed:
                    messages.success(request, 'Successfully borrowed {0} items.'.format(str(borrowed)))
                if returned:
                    messages.success(request, 'Successfully returned {0} items.'.format(str(returned)))
            else:
                messages.error(request, 'There was an error submitted the form. Please check the fields and try again.')
        return redirect('library:form-view', pk=pk)

    if context['form'] is None:
        context['form'] = ExternalBorrowingLibrarianForm(display_form=external_borrow_form)

    return render(request, 'library/external_form_view.html', context)
