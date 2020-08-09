from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import RegistrationEmail, SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from .models import Member


def signup(request):
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
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
			return HttpResponse('Please confirm your email address to complete the registration.')
	else:
		form = SignupForm()
	return render(request, 'members/signup.html', {'form': form})


def activate(request, uidb64, token):
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


def index(request):
	return render(request, 'members/index.html')


def register(request):
	if request.method == "POST":
		# Handle the processing of the form
		form = RegistrationEmail(request.POST)
		message = "If a gatekeeper exists with that email address. they will be sent an email with further instructions."
		debugmessage = ""
		if form.is_valid():
			reg_email = form.cleaned_data['reg_email']
			try:
				member = Member.objects.get(email_address=reg_email)
				debugmessage += "Found member %s. \n" % str(member)
			except Member.DoesNotExist:
				# No member found with that email address. Don't tell them that though.
				member = None
				debugmessage += "No member found with email of %s. \n" % reg_email
			if member:
				# Check permissions here - only send if gatekeeper.
				send_mail('Test Email', 'This is a test message.', 'donald@sutherland.id.au', [reg_email], fail_silently=False)
				pass
			message = "You attempted to sign up with this email: %s" % reg_email + "\n" + message
			if settings.DEBUG:
				message += "\n %s" % debugmessage
			return render(request, 'members/RegFormOne.html', {'form': form, 'message': message})
		else:
			message = "That email address was not valid. Please try again."
			return render(request, 'members/RegFormOne.html', {'form': form, 'message': message})
	else:
		# Render an empty form
		form = RegistrationEmail()
		return render(request, 'members/RegFormOne.html', {'form': form})


def login(request):
	return HttpResponse("You will be able to login here!")
