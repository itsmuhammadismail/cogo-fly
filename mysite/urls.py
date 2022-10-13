from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('seo', include('seo.urls')),
]

#THIS IS A QUICK FIX PLEASE REMOVE IT WHEN FRENCH TRANSLATION IS DONE
urlpatterns += [re_path(r'^fr/(?P<url>.*)$', RedirectView.as_view(url='/en/%(url)s'))]

urlpatterns += i18n_patterns(
    path('', include('cogofly.urls')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog')
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
