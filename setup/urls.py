from django.contrib import admin
from django.urls import path
from portaria.views import home  # Importamos nossa view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'), # A rota vazia '' significa a página inicial
]