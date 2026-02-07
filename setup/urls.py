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
    exportar_relatorio_solicitacoes,
    historico_encomendas,
    historico_solicitacoes,
    api_stats
)

# Views do Portal do Morador
from portaria.views_morador import (
    portal_home,
    minhas_encomendas,
    minhas_solicitacoes,
    nova_solicitacao,
    ver_solicitacao,
    avisos
)

# Views do Portal do Síndico
from portaria.views_sindico import (
    portal_sindico_home,
    selecionar_condominio,
    criar_condominio,
    painel_sindico,
    moradores_sindico,
    visitantes_sindico,
    registrar_saida_sindico,
    encomendas_sindico,
    entregar_encomenda_sindico,
    solicitacoes_sindico,
    responder_solicitacao_sindico,
    dashboard_condominio
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
    path('api/stats/', api_stats, name='api_stats'),
    path('exportar_relatorio/', exportar_relatorio, name='exportar_relatorio'),
    
    # --- Portal do Morador ---
    path('morador/', portal_home, name='morador_home'),
    path('morador/encomendas/', minhas_encomendas, name='morador_encomendas'),
    path('morador/solicitacoes/', minhas_solicitacoes, name='morador_solicitacoes'),
    path('morador/solicitacoes/nova/', nova_solicitacao, name='morador_nova_solicitacao'),
    path('morador/solicitacoes/<int:id>/', ver_solicitacao, name='morador_ver_solicitacao'),
    path('morador/avisos/', avisos, name='morador_avisos'),
    
    # --- Portal do Síndico ---
    path('sindico/', portal_sindico_home, name='sindico_home'),
    path('sindico/selecionar/<int:condominio_id>/', selecionar_condominio, name='sindico_selecionar'),
    path('sindico/novo-condominio/', criar_condominio, name='sindico_criar_condominio'),
    path('sindico/painel/', painel_sindico, name='sindico_painel'),
    path('sindico/moradores/', moradores_sindico, name='sindico_moradores'),
    path('sindico/visitantes/', visitantes_sindico, name='sindico_visitantes'),
    path('sindico/visitantes/saida/<int:visitante_id>/', registrar_saida_sindico, name='sindico_registrar_saida'),
    path('sindico/encomendas/', encomendas_sindico, name='sindico_encomendas'),
    path('sindico/encomendas/entregar/<int:encomenda_id>/', entregar_encomenda_sindico, name='sindico_entregar_encomenda'),
    path('sindico/solicitacoes/', solicitacoes_sindico, name='sindico_solicitacoes'),
    path('sindico/solicitacoes/responder/<int:solicitacao_id>/', responder_solicitacao_sindico, name='sindico_responder_solicitacao'),
    # Compatibilidade com rota antiga
    path('sindico/condominio/<int:condominio_id>/', dashboard_condominio, name='sindico_dashboard'),
]

# Configuração para arquivos de mídia (Fotos/Uploads) em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Servir a pasta /img/ para logotipos
    urlpatterns += static('/img/', document_root=settings.BASE_DIR / 'img')