from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from .forms import SignupForm, LoginForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from .models import Member
from .decorators import gatekeeper_required, switch_to_proxy
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.db.models import Q, F


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
				message = render_to_string('members/acc_active_email.html', {
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
			return render(request, 'members/signup.html', {'form': form})
	else:
		form = SignupForm()
		return render(request, 'members/signup.html', {'form': form})


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
	template_name = 'members/login.html'
	authentication_form = LoginForm


@method_decorator(gatekeeper_required, name='dispatch')
class MemberListView(ListView):
	model = Member
	context_object_name = 'members'

	def get_template_names(self):
		return ['members/member_list_gatekeeper.html']

	def get_queryset(self):
		name_search = self.request.GET.get('name', None)
		has_notes = self.request.GET.get('has_notes', None)
		queryset = Member.objects.all()
		if name_search is not None:
			queryset = queryset.filter(
				Q(first_name__icontains=name_search) |
				Q(last_name__icontains=name_search) |
				Q(preferred_name__icontains=name_search)
			)
		if (has_notes is not None) and (switch_to_proxy(self.request.user).is_committee is True):
			pass
		return queryset
