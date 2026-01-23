from django.contrib import admin
from django.urls import path, include # <--- Importe 'include' aqui
from portaria.views import home, registrar_saida

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Esta linha cria automaticamente as rotas de login/logout
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('', home, name='home'),
    path('saida/<int:id_visitante>/', registrar_saida, name='registrar_saida'),
]