from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
	path('list/', views.MemberListView.as_view(), name='member-list'),
	path('signup/', views.SignupHomeView.as_view(), name='signup-home'),
	path('signup/existing_member/start/', views.old_member_signup_redirect, name='signup-old-start'),
	path('signup/existing_member/<int:pk>/', views.old_membership_view, name='signup-old'),
	path('signup/existing_member/', views.old_membership_view, name='signup-old'),
	path('signup/new_member/', views.new_membership_view, name='signup-new'),
	path('profile/<int:pk>/', views.MemberProfileView.as_view(), name='profile'),
	path('auto/', views.MemberAutocomplete.as_view(), name='autocomplete'),
	path('email_prefs/<uidb64>/<token>/', views.email_preferences_view, name='email-prefs-token'),
	path('email_prefs/', views.email_preferences_view, name='email-prefs'),
]
