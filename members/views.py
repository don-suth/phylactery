from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from .forms import SignupForm, LoginForm, MembershipForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from .models import Member
from .decorators import gatekeeper_required
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from .admin import MemberListAdmin
from django.contrib.admin import AdminSite
from django.views.generic import TemplateView


def signup_view(request):
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			reg_email = form.cleaned_data['email']
			try:
				member = Member.objects.get(email_address=reg_email)
			except Member.DoesNotExist:
				member = None
			if member is not None and member.has_rank("GATEKEEPER"):
				# Member exists and they are a gatekeeper - sign them up!
				user = form.save(commit=False)
				user.is_active = False
				user.save()
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
	paginate_by = 100
	adm_model = MemberListAdmin(Member, AdminSite())
	changelist = None
	template_name = "members/member_list.html"
	context_object_name = 'members'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		self.changelist = self.adm_model.get_changelist_instance(self.request)

		context['cl'] = self.changelist
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
				print(qs)
		try:
			qs = qs.filter(**remaining_lookup_params)
			print(qs)
		except:
			pass

		# Set ordering.
		ordering = self.changelist.get_ordering(self.request, qs)
		qs = qs.order_by(*ordering)

		# Apply search results
		qs, search_use_distinct = self.changelist.model_admin.get_search_results(self.request, qs, self.changelist.query)
		print(qs)
		return qs


def new_membership_view(request):
	if request.method == 'POST':
		form = MembershipForm(request.POST)
		if form.is_valid():
			return HttpResponse(str(request.POST))
	else:
		form = MembershipForm()
	return render(request, 'members/membershipform.html', {'form': form})


class SignupHomeView(TemplateView):
	template_name = 'members/signup_start.html'
