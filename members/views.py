from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

from .forms import RegistrationEmail
from .models import Member


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
				# Check permissions and send email here.
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
