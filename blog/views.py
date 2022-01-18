from django.shortcuts import render, redirect
from django.http import Http404
from django.views import generic
from .models import BlogPost
from members.models import switch_to_proxy
from django.utils import timezone

class AllBlogPostsView(generic.ListView):
    template_name = 'blog/blog_list_view.html'
    context_object_name = 'blogpost_list'
    model = BlogPost
    paginate_by = 10

    def get_queryset(self):
        return BlogPost.objects.filter(
            publish_on__lte=timezone.now()
        ).order_by('-publish_on')

    def get(self, request, *args, **kwargs):
        u = switch_to_proxy(request.user)
        if (not self.request.user.is_authenticated) or (not u.is_committee):
            self.object_list = self.get_queryset()
        else:
            self.object_list = BlogPost.objects.order_by('-publish_on')
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_('Empty list and “%(class_name)s.allow_empty” is False.') % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data()
        return self.render_to_response(context)


class BlogPostDetailView(generic.DetailView):
    model = BlogPost
    template_name = 'blog/blog_detail_view.html'
    slug_field = 'slug_title'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_published is False:
            u = switch_to_proxy(request.user)
            if (not self.request.user.is_authenticated) or (not u.is_committee):
                raise Http404('No blog posts found matching your query.')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)