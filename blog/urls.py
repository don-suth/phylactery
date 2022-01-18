from django.urls import path
from . import views

app_name = 'blog'
urlpatterns = [
    path('post/<int:pk>/', views.BlogPostDetailView.as_view(), name='detail-id'),
    path('', views.AllBlogPostsView.as_view(), name='blog-home'),
]