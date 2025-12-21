from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from products.home_views import home
from ai_features.views import virtual_tryon_demo

# def home(request):
#     return HttpResponse("Home Page - Login Successful")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('carts.urls')),
    path('orders/', include('orders.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('ai/', include('ai_features.urls')),
    path('virtual-tryon/', virtual_tryon_demo, name='virtual_tryon_demo'),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
