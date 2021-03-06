from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView
from .forms import SignupForm, LoginForm, NewMembershipForm, OldMembershipForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from .models import Member, Membership, MemberFlag, switch_to_proxy
from .decorators import gatekeeper_required
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from .admin import MemberListAdmin
from django.contrib.admin import AdminSite
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from dal import autocomplete
from django.db.models import Q
from library.models import BorrowRecord
import datetime


def signup_view(request):
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			reg_email = form.cleaned_data['email']
			try:
				member = Member.objects.get(email_address=reg_email)
			except Member.DoesNotExist:
				member = None
			if member is not None and (member.has_rank("GATEKEEPER") or member.has_rank("COMMITTEE")):
				# Member exists and they are a gatekeeper/committee member - sign them up!
				user = form.save(commit=False)
				user.is_active = False
				user.save()
				member.user = user
				member.save()
				current_site = get_current_site(request)
				mail_subject = 'Activate your Unigames account.'
				message = render_to_string('account/acc_active_email.html', {
					'user': user,
					'domain': current_site.domain,
					'uid': urlsafe_base64_encode(force_bytes(user.pk)),
					'token': account_activation_token.make_token(user),
				})
				to_email = form.cleaned_data.get('email')
				email = EmailMessage(
					mail_subject, message, to=[to_email]
				)
				email.send()
			else:
				# The form is valid, but the member either doesn't exist or is not a gatekeeper.
				# We give them the same response, but don't do anything with the data to prevent leaking.
				pass
			return HttpResponse("""
			Form submission complete.
			If you are a gatekeeper, an email to confirm your registration will sent to the specified email address.
			If you didn't receive an email, try checking your spam box. If you suspect an error has been made,
			contact an admin.""")
		else:
			return render(request, 'account/signup.html', {'form': form})
	else:
		form = SignupForm()
		return render(request, 'account/signup.html', {'form': form})


def activate_view(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except(TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None
	if user is not None and account_activation_token.check_token(user, token):
		user.is_active = True
		user.save()
		return HttpResponse('Thank you for your email confirmation. Now you can log in to your account.')
	else:
		return HttpResponse('Activation link is invalid!')


class MyLoginView(LoginView):
	template_name = 'account/login.html'
	authentication_form = LoginForm


@method_decorator(gatekeeper_required, name='dispatch')
class MemberListView(ListView):
	"""
	For filtering, it pulls out all of the active filters on MemberAdmin,
	runs the queryset through all of those, then turns that queryset into
	the resulting listview.
	Templates of the view can be customised here,
	Templates of the filter are customised in admin.py
	"""
	model = Member
	adm_model = MemberListAdmin(Member, AdminSite())
	changelist = None
	template_name = "members/member_list.html"
	context_object_name = 'members'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		self.changelist = self.adm_model.get_changelist_instance(self.request)
		context['cl'] = self.changelist

		paginator = Paginator(self.object_list, 100)  # Show 100 members per page.

		# The shenanigans involving +1s and -1s is to avoid a conflict with the admin changelist
		# Essentially, the url page number is 0-indexed, while paginator is 1-indexed
		page_number = int(self.request.GET.get('p', '0')) + 1
		page_obj = paginator.get_page(page_number)
		context['page_obj'] = page_obj

		first_page, last_page = paginator.page_range
		prev_page = page_number - 2
		next_page = page_number

		context['first_page_q'] = self.changelist.get_query_string(new_params={'p': first_page})
		context['prev_page_q'] = self.changelist.get_query_string(new_params={'p': prev_page})
		context['next_page_q'] = self.changelist.get_query_string(new_params={'p': next_page})
		context['last_page_q'] = self.changelist.get_query_string(new_params={'p': last_page})

		return context

	def get_queryset(self):
		qs = super().get_queryset()
		get_params = self.request.GET.dict()

		self.changelist = self.adm_model.get_changelist_instance(self.request)
		(self.changelist.filter_specs, self.changelist.has_filters, remaining_lookup_params,
			filters_use_distinct, has_filters) = self.changelist.get_filters(self.request)

		# Then, we let every list filter modify the queryset to its liking.
		qs = self.changelist.root_queryset
		for filter_spec in self.changelist.filter_specs:
			new_qs = filter_spec.queryset(self.request, qs)
			if new_qs is not None:
				qs = new_qs


		# Set ordering.
		ordering = self.changelist.get_ordering(self.request, qs)
		qs = qs.order_by(*ordering)

		# Apply search results
		qs, search_use_distinct = self.changelist.model_admin.get_search_results(self.request, qs, self.changelist.query)

		return qs


@gatekeeper_required
def new_membership_view(request):
	if request.method == 'POST':
		form = NewMembershipForm(request.POST)
		if form.is_valid():
			try:
				authorising_gatekeeper = request.user.member
			except Member.DoesNotExist:
				authorising_gatekeeper = None

			if Member.objects.filter(email_address=form.cleaned_data['email']).exists():
				form.add_error('email', "This email is already in use. Are you sure you're a fresher?")
				return render(request, 'members/new_membership_form.html', {'form': form})

			new_member = Member(
				first_name=form.cleaned_data['first_name'],
				last_name=form.cleaned_data['last_name'],
				preferred_name=form.cleaned_data['preferred_name'],
				pronouns=form.cleaned_data['pronouns'],
				student_number=form.cleaned_data['student_number'],
				email_address=form.cleaned_data['email'],
				receive_emails=form.cleaned_data['receive_emails'],
			)

			if form.cleaned_data['is_fresher'] is True:
				new_member.join_date = datetime.date.today()

			new_membership = Membership(
				member=new_member,
				guild_member=form.cleaned_data['is_guild'],
				phone_number=form.cleaned_data['phone_number'],
				expired=False,
				amount_paid=form.cleaned_data['amount_paid'],
				authorising_gatekeeper=authorising_gatekeeper
			)
			new_member.save()
			new_membership.save()

			# Add in the extra MemberFlag fields
			for flag_pk in form.extra_fields:
				flag_val = form.cleaned_data.get('flag_' + str(flag_pk), False)
				if flag_val:
					MemberFlag.objects.get(pk=flag_pk).member.add(new_member)

			messages.success(request, "Successfully added "+str(new_member))
			return redirect('members:signup-home')
	else:
		form = NewMembershipForm()
	return render(request, 'members/new_membership_form.html', {'form': form})


@gatekeeper_required
def old_membership_view(request, pk=None):
	"""
	Covers the handling of new memberships for existing members.
	"""
	if request.method == 'GET':
		member = get_object_or_404(Member, pk=pk)
		# We have our member, render a membership form with most details filled out

		if member.bought_membership_this_year:
			messages.error(request, "This member already bought a membership this year.")
			return redirect('members:profile', pk=pk)

		data = {
			'first_name': member.first_name,
			'last_name': member.last_name,
			'preferred_name': member.preferred_name,
			'pronouns': member.pronouns,
			'student_number': member.student_number,
			'email': member.email_address,
			'receive_emails': member.receive_emails,
		}

		recent_membership = member.get_most_recent_membership()
		if recent_membership:
			data['is_guild'] = recent_membership.guild_member

		form = OldMembershipForm(data)

		form.errors['phone_number'] = ['For your privacy, please enter your phone number again.']
		form.add_error('is_guild', 'Please verify that this is still correct.')
		form.helper.layout[0][0].legend = "Check that your details are correct, {{ member.first_name }}."
		request.session['editing_member_id'] = pk
		return render(request, 'members/old_membership_form.html', {'form': form, 'member': member})
	if request.method == 'POST':
		if request.session.get('editing_member_id', None) is None:
			return redirect('members:signup-home')
		else:
			pk = request.session.get('editing_member_id')
			del request.session['editing_member_id']
			member = get_object_or_404(Member, pk=pk)

			if member.bought_membership_this_year:
				messages.error(request, "This member already bought a membership this year.")
				return redirect('members:profile', pk=pk)

			init = {
				'first_name': member.first_name,
				'last_name': member.last_name,
				'preferred_name': member.preferred_name,
				'pronouns': member.pronouns,
				'student_number': member.student_number,
				'email': member.email_address,
				'receive_emails': member.receive_emails
			}
			form = OldMembershipForm(request.POST, initial=init)

			if form.is_valid():
				if form.cleaned_data['email'] != member.email_address:
					if Member.objects.filter(email_address=form.cleaned_data['email']).exists():
						form.add_error('email', "This email is already in use. Are you sure you're a fresher?")
						form.helper.layout[0][0].legend = "Check that your details are correct, {{ member.first_name }}."
						return render(request, 'members/old_membership_form.html', {'form': form})
				if form.has_changed():
					member.first_name = form.cleaned_data['first_name']
					member.last_name = form.cleaned_data['last_name']
					member.preferred_name = form.cleaned_data['preferred_name']
					member.pronouns = form.cleaned_data['pronouns']
					member.student_number = form.cleaned_data['student_number']
					member.email_address = form.cleaned_data['email']
					member.receive_emails = form.cleaned_data['receive_emails']
					member.save()

				try:
					authorising_gatekeeper = request.user.member
				except Member.DoesNotExist:
					authorising_gatekeeper = None

				new_membership = Membership(
					member=member,
					guild_member=form.cleaned_data['is_guild'],
					phone_number=form.cleaned_data['phone_number'],
					expired=False,
					amount_paid=form.cleaned_data['amount_paid'],
					authorising_gatekeeper=authorising_gatekeeper
				)
				new_membership.save()

				# Add in the extra MemberFlag fields
				for flag_pk in form.extra_fields:
					flag_val = form.cleaned_data.get('flag_' + str(flag_pk), None)
					if flag_val is False:
						MemberFlag.objects.get(pk=flag_pk).member.remove(member)
					elif flag_val is True:
						MemberFlag.objects.get(pk=flag_pk).member.add(member)

				messages.success(request, "New membership added for {0}!".format(member.first_name))
				return redirect('members:profile', pk=pk)
			else:
				form.helper.layout[0][0].legend = "Check that your details are correct, {{ member.first_name }}."
				return render(request, 'members/old_membership_form.html', {'form': form})


@method_decorator(gatekeeper_required, name='dispatch')
class SignupHomeView(TemplateView):
	template_name = 'members/signup_start.html'


@gatekeeper_required
def old_member_signup_redirect(request):
	messages.info(
		request,
		"Search for the member in the list below, go to their profile, and click the 'New Membership' button."
	)
	return redirect('members:member-list')


@method_decorator(gatekeeper_required, name='dispatch')
class MemberProfileView(DetailView):
	template_name = 'members/profile.html'
	model = Member

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['borrowed_items'] = BorrowRecord.objects.filter(
			borrowing_member=self.object,
			date_returned=None,
		)
		context['today'] = datetime.date.today()
		return context


class MemberAutocomplete(autocomplete.Select2QuerySetView):
	def get_queryset(self):
		u = switch_to_proxy(self.request.user)
		if u.is_authenticated and u.is_gatekeeper:
			qs = Member.objects.all()
		else:
			qs = Member.objects.none()
		if self.q:
			qs = qs.filter(Q(first_name__icontains=self.q) | Q(last_name__icontains=self.q))
		return qs
