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
from .views import control_panel_view

urlpatterns = [
    path('', TemplateView.as_view(template_name='phylactery/home.html'), name='home'),
    path('faq/', TemplateView.as_view(template_name='phylactery/faq.html'), name='faq'),
    path('events/', TemplateView.as_view(template_name='phylactery/events.html'), name='events'),
    path('roleplaying/', TemplateView.as_view(template_name='phylactery/roleplaying.html'), name='roleplaying'),
    path('members/', include(('members.membership_urls', 'members'), namespace='members')),
    path('account/', include(('members.account_urls', 'members'), namespace='account')),
    path('library/', include('library.urls')),
    path('control-panel/', control_panel_view, name='control-panel'),
    path('admin/', admin.site.urls),
    path('jsi18n/', JavaScriptCatalog.as_view())
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)