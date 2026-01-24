from django.contrib import admin
from django.urls import path, include
from portaria.views import home, registrar_saida, registrar_encomenda, confirmar_entrega, exportar_relatorio, exportar_relatorio_encomendas, marcar_notificado, historico_encomendas

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', home, name='home'),
    path('saida/<int:id_visitante>/', registrar_saida, name='registrar_saida'),
    path('nova-encomenda/', registrar_encomenda, name='registrar_encomenda'),
    path('entregar-encomenda/<int:id_encomenda>/', confirmar_entrega, name='confirmar_entrega'),
    path('relatorio/', exportar_relatorio, name='exportar_relatorio'),
    path('relatorio-encomendas/', exportar_relatorio_encomendas, name='exportar_relatorio_encomendas'),
    path('notificar/<int:id_encomenda>/', marcar_notificado, name='marcar_notificado'),
    path('historico-encomendas/', historico_encomendas, name='historico_encomendas'),
]