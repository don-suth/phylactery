from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
	path('signup/', views.signup_view, name='signup'),
	path('activate/<uidb64>/<token>/', views.activate_view, name='activate'),
	path('login/', views.MyLoginView.as_view(), name='login'),
	path('logout/', LogoutView.as_view(), name='logout'),
	path('list/', views.MemberListView.as_view(), name='member_list')
	# path('password_change/', views.PasswordChangeView.as_view(), name='password_change'),
	# path('password_change/done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
	# path('password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
	# path('password_reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
	# path('reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
	# path('reset/done/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
