from django.urls import path
from . import views

app_name = 'blog'
urlpatterns = [
    path('post/<int:pk>/', views.BlogPostDetailView.as_view(), name='detail-id'),
    path('post/<slug:slug>/', views.BlogPostDetailView.as_view(), name='detail-slug'),
    path('', views.AllBlogPostsView.as_view(), name='blog-home'),
]