from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'account'
urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate_view, name='activate'),
    path('login/', views.MyLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_change/', views.MyPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', views.my_password_change_done_view, name='password_change_done'),
    path('password_reset/', views.MyPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.MyPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),

]
