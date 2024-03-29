"""phylactery URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from .views import control_panel_view, HomeView, CommitteeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('faq/', TemplateView.as_view(template_name='phylactery/faq.html'), name='faq'),
    path('events/', TemplateView.as_view(template_name='phylactery/events.html'), name='events'),
    path('committee/', CommitteeView.as_view(), name='committee'),
    path('contact_us/', TemplateView.as_view(template_name='phylactery/contact_us.html'), name='contact'),
    path('life_members/', TemplateView.as_view(template_name='phylactery/life_members.html'), name='life_members'),
    path('constitution/', TemplateView.as_view(template_name='phylactery/constitution.html'), name='constitution'),
    path('regulations/', TemplateView.as_view(template_name='phylactery/regulations.html'), name='regulations'),
    path('roleplaying/', TemplateView.as_view(template_name='phylactery/roleplaying.html'), name='roleplaying'),
    path('api/items/', include(('library.api_urls', 'library'), namespace='api-library')),
    path('api/', TemplateView.as_view(template_name='phylactery/api.html'), name='api-home'),
    path('members/', include(('members.membership_urls', 'members'), namespace='members')),
    path('account/', include(('members.account_urls', 'members'), namespace='account')),
    path('library/', include('library.urls')),
    path('blog/', include('blog.urls')),
    path('control-panel/', control_panel_view, name='control-panel'),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('jsi18n/', JavaScriptCatalog.as_view())
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)