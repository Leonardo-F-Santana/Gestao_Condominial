from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

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

    exportar_relatorio, 
    exportar_relatorio_encomendas, 
    exportar_relatorio_solicitacoes,
    historico_encomendas,
    historico_solicitacoes,
    api_stats,
    alterar_senha,
    cadastro_morador
)

# Views do Portal do Morador
from portaria.views_morador import (
    portal_home,
    minhas_encomendas,
    minhas_solicitacoes,
    nova_solicitacao,
    ver_solicitacao,
    avisos,
    areas_disponiveis,
    fazer_reserva,
    minhas_reservas,
    cancelar_reserva
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
    avisos_sindico,
    criar_aviso_sindico,
    editar_aviso_sindico,
    excluir_aviso_sindico,
    resetar_senha_morador,
    dashboard_condominio,
    areas_comuns_sindico,
    excluir_area_sindico,
    reservas_sindico,
    aprovar_reserva_sindico,
    recusar_reserva_sindico
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- Rota Principal e Autenticação ---
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('alterar-senha/', alterar_senha, name='alterar_senha'),
    path('cadastro/<uuid:codigo_convite>/', cadastro_morador, name='cadastro_morador'),
    
    # --- Recuperação de Senha ---
    path('recuperar-senha/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/recuperar-senha/enviado/',
    ), name='password_reset'),
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('recuperar-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/recuperar-senha/concluido/',
    ), name='password_reset_confirm'),
    path('recuperar-senha/concluido/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
    
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

    path('api/stats/', api_stats, name='api_stats'),
    path('exportar_relatorio/', exportar_relatorio, name='exportar_relatorio'),
    
    # --- Portal do Morador ---
    path('morador/', portal_home, name='morador_home'),
    path('morador/encomendas/', minhas_encomendas, name='morador_encomendas'),
    path('morador/solicitacoes/', minhas_solicitacoes, name='morador_solicitacoes'),
    path('morador/solicitacoes/nova/', nova_solicitacao, name='morador_nova_solicitacao'),
    path('morador/solicitacoes/<int:id>/', ver_solicitacao, name='morador_ver_solicitacao'),
    path('morador/avisos/', avisos, name='morador_avisos'),
    path('morador/reservas/', minhas_reservas, name='morador_reservas'),
    path('morador/reservas/areas/', areas_disponiveis, name='morador_areas_disponiveis'),
    path('morador/reservas/nova/<int:area_id>/', fazer_reserva, name='morador_fazer_reserva'),
    path('morador/reservas/<int:reserva_id>/cancelar/', cancelar_reserva, name='morador_cancelar_reserva'),
    
    # --- Portal do Síndico ---
    path('sindico/', portal_sindico_home, name='sindico_home'),
    path('sindico/selecionar/<int:condominio_id>/', selecionar_condominio, name='sindico_selecionar'),
    path('sindico/novo-condominio/', criar_condominio, name='sindico_criar_condominio'),
    path('sindico/painel/', painel_sindico, name='sindico_painel'),
    path('sindico/moradores/', moradores_sindico, name='sindico_moradores'),
    path('sindico/moradores/<int:morador_id>/resetar-senha/', resetar_senha_morador, name='sindico_resetar_senha'),
    path('sindico/visitantes/', visitantes_sindico, name='sindico_visitantes'),
    path('sindico/visitantes/saida/<int:visitante_id>/', registrar_saida_sindico, name='sindico_registrar_saida'),
    path('sindico/encomendas/', encomendas_sindico, name='sindico_encomendas'),
    path('sindico/encomendas/entregar/<int:encomenda_id>/', entregar_encomenda_sindico, name='sindico_entregar_encomenda'),
    path('sindico/solicitacoes/', solicitacoes_sindico, name='sindico_solicitacoes'),
    path('sindico/solicitacoes/responder/<int:solicitacao_id>/', responder_solicitacao_sindico, name='sindico_responder_solicitacao'),
    path('sindico/avisos/', avisos_sindico, name='sindico_avisos'),
    path('sindico/avisos/novo/', criar_aviso_sindico, name='sindico_criar_aviso'),
    path('sindico/avisos/<int:aviso_id>/editar/', editar_aviso_sindico, name='sindico_editar_aviso'),
    path('sindico/avisos/<int:aviso_id>/excluir/', excluir_aviso_sindico, name='sindico_excluir_aviso'),
    # Compatibilidade com rota antiga
    path('sindico/areas-comuns/', areas_comuns_sindico, name='sindico_areas_comuns'),
    path('sindico/areas-comuns/<int:area_id>/excluir/', excluir_area_sindico, name='sindico_excluir_area'),
    path('sindico/reservas/', reservas_sindico, name='sindico_reservas'),
    path('sindico/reservas/<int:reserva_id>/aprovar/', aprovar_reserva_sindico, name='sindico_aprovar_reserva'),
    path('sindico/reservas/<int:reserva_id>/recusar/', recusar_reserva_sindico, name='sindico_recusar_reserva'),
    # Compatibilidade com rota antiga
    path('sindico/condominio/<int:condominio_id>/', dashboard_condominio, name='sindico_dashboard'),
]

# Configuração para arquivos de mídia (Fotos/Uploads) em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Servir a pasta /img/ para logotipos
    urlpatterns += static('/img/', document_root=settings.BASE_DIR / 'img')