from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
	path('list/', views.MemberListView.as_view(), name='member_list'),
	path('signup/', views.SignupHomeView.as_view(), name='signup-home'),
	path('signup/existing_member/', views.new_membership_view, name='signup-old'),
	path('signup/new_member/', views.new_membership_view, name='signup-new'),
]
