from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from portaria.views import (
    home, 
    registrar_saida, 
    registrar_encomenda, 
    confirmar_entrega, 
    historico_encomendas, 
    exportar_relatorio,
    exportar_relatorio_encomendas,
    marcar_notificado,
    registrar_solicitacao # <--- IMPORTANTE: Adicione essa importação
)

urlpatterns = [
    # Admin e Login
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Home e Visitantes
    path('', home, name='home'),
    path('saida/<int:id_visitante>/', registrar_saida, name='registrar_saida'),
    
    # Encomendas
    path('nova-encomenda/', registrar_encomenda, name='registrar_encomenda'),
    path('confirmar-entrega/<int:id_encomenda>/', confirmar_entrega, name='confirmar_entrega'),
    path('historico-encomendas/', historico_encomendas, name='historico_encomendas'),
    path('marcar-notificado/<int:id_encomenda>/', marcar_notificado, name='marcar_notificado'),

    # Solicitações (A ROTA QUE FALTAVA) 👇
    path('registrar-solicitacao/', registrar_solicitacao, name='registrar_solicitacao'),

    # Relatórios PDF
    path('relatorio-visitantes/', exportar_relatorio, name='exportar_relatorio'),
    path('relatorio-encomendas/', exportar_relatorio_encomendas, name='exportar_relatorio_encomendas'),
]