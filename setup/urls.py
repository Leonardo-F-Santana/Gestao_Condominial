from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Importando TODAS as views necessárias
from portaria.views import (
    home, 
    login_view, 
    logout_view, 
    registrar_visitante, 
    registrar_encomenda, 
    confirmar_entrega, 
    marcar_notificado, 
    registrar_solicitacao, 
    registrar_saida, 
    dashboard, 
    exportar_relatorio, 
    exportar_relatorio_encomendas, 
    exportar_relatorio_solicitacoes, # Novo
    historico_encomendas,
    historico_solicitacoes # Novo
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- Rota Principal e Autenticação ---
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # --- Ações de Visitantes ---
    path('registrar_visitante/', registrar_visitante, name='registrar_visitante'),
    path('registrar_saida/<int:id_visitante>/', registrar_saida, name='registrar_saida'),
    
    # --- Ações de Encomendas ---
    path('registrar_encomenda/', registrar_encomenda, name='registrar_encomenda'),
    path('confirmar_entrega/<int:id_encomenda>/', confirmar_entrega, name='confirmar_entrega'),
    path('marcar_notificado/<int:id_encomenda>/', marcar_notificado, name='marcar_notificado'),
    path('historico_encomendas/', historico_encomendas, name='historico_encomendas'),
    path('exportar_relatorio_encomendas/', exportar_relatorio_encomendas, name='exportar_relatorio_encomendas'),
    
    # --- Ações de Solicitações (Ocorrências) ---
    path('registrar_solicitacao/', registrar_solicitacao, name='registrar_solicitacao'),
    path('historico_solicitacoes/', historico_solicitacoes, name='historico_solicitacoes'),
    path('exportar_relatorio_solicitacoes/', exportar_relatorio_solicitacoes, name='exportar_relatorio_solicitacoes'),
    
    # --- Gestão e Relatórios Gerais ---
    path('dashboard/', dashboard, name='dashboard'),
    path('exportar_relatorio/', exportar_relatorio, name='exportar_relatorio'),
]

# Configuração para arquivos de mídia (Fotos/Uploads) em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)