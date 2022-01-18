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
        ).order_by('publish_on')


class BlogPostDetailView(generic.DetailView):
    model = BlogPost
    template_name = 'blog/blog_detail_view.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_published is False:
            u = switch_to_proxy(request.user)
            if (not self.request.user.is_authenticated) or (not u.is_committee):
                raise Http404('No blog posts found matching your query.')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)