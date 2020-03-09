from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render

def index(request):
	return HttpResponse("Hello, world. You're at the members index.")


def register(request):
	if request.method == "POST":
		# Handle the processing of the form
		pass()
	else:
		# Render an empty form
		pass()


def login(request):
	return HttpResponse("You will be able to login here!")
