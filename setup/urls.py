from django.contrib import admin
from django.urls import path, include
from portaria.views import home, registrar_saida, registrar_encomenda, confirmar_entrega # <--- Importe as novas views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('', home, name='home'),
    path('saida/<int:id_visitante>/', registrar_saida, name='registrar_saida'),
    

    path('nova-encomenda/', registrar_encomenda, name='registrar_encomenda'),
    path('entregar-encomenda/<int:id_encomenda>/', confirmar_entrega, name='confirmar_entrega'),
]