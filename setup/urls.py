from django.contrib import admin

from django.urls import path, include

from django.conf import settings

from django.conf.urls.static import static

from django.contrib.auth import views as auth_views





from portaria.views import (

    home, 

    login_view, 

    popup_close,

    logout_view, 

    registrar_visitante, 

    registrar_encomenda, 

    confirmar_entrega, 

    marcar_notificado, 

    registrar_solicitacao, 

    registrar_saida, 

    trocar_condominio,



    exportar_relatorio, 

    exportar_relatorio_encomendas, 

    exportar_relatorio_solicitacoes,

    historico_encomendas,

    historico_solicitacoes,

    mensagens_portaria,

    api_stats,

    alterar_senha,

    cadastro_morador,

    api_moradores_offline,

    api_sync_offline,

    CustomPasswordResetView,

    salvar_inscricao_push,

    remover_subscricao,

    liberar_acesso_reserva

)





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

    cancelar_reserva,

    mensagens,

    ocorrencias,

    minhas_cobrancas,

    editar_perfil_morador,

    documentos_morador,

    completar_cadastro,

    atualizar_preferencia_push,

    feedback_morador

)





from portaria.views_sindico import (

    portal_sindico_home,

    selecionar_condominio,

    criar_condominio,

    painel_sindico,

    moradores_sindico,

    sindico_morador_editar,

    sindico_morador_excluir,

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

    recusar_reserva_sindico,

    financeiro_sindico,

    buscar_moradores_ajax,

    mensagens_sindico,

    ocorrencias_sindico,

    alterar_status_ocorrencia,

    editar_perfil_sindico,

    sindico_notificacoes,

    documentos_sindico,

    redirecionar_notificacao,

    gerar_advertencia_pdf,

    gerenciar_portaria,

    central_tarefas_sindico,

    feedbacks_sindico

)



urlpatterns = [

    path('admin/', admin.site.urls),

    path('accounts/', include('allauth.urls')),





    path('', home, name='home'),

    path('login/', login_view, name='login'),

    path('login/popup-close/', popup_close, name='popup_close'),

    path('logout/', logout_view, name='logout'),

    path('alterar-senha/', alterar_senha, name='alterar_senha'),

    path('cadastro/<uuid:codigo_convite>/', cadastro_morador, name='cadastro_morador'),

    path('trocar-condominio/<int:condominio_id>/', trocar_condominio, name='trocar_condominio'),





    path('recuperar-senha/', CustomPasswordResetView.as_view(

        template_name='registration/password_reset_form.html',

        email_template_name='registration/password_reset_email.txt',

        html_email_template_name='registration/password_reset_email.html',

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





    path('registrar_visitante/', registrar_visitante, name='registrar_visitante'),

    path('registrar_saida/<int:id_visitante>/', registrar_saida, name='registrar_saida'),





    path('registrar_encomenda/', registrar_encomenda, name='registrar_encomenda'),

    path('confirmar_entrega/<int:id_encomenda>/', confirmar_entrega, name='confirmar_entrega'),

    path('marcar_notificado/<int:id_encomenda>/', marcar_notificado, name='marcar_notificado'),

    path('historico_encomendas/', historico_encomendas, name='historico_encomendas'),

    path('exportar_relatorio_encomendas/', exportar_relatorio_encomendas, name='exportar_relatorio_encomendas'),





    path('registrar_solicitacao/', registrar_solicitacao, name='registrar_solicitacao'),

    path('historico_solicitacoes/', historico_solicitacoes, name='historico_solicitacoes'),

    path('exportar_relatorio_solicitacoes/', exportar_relatorio_solicitacoes, name='exportar_relatorio_solicitacoes'),

    path('liberar_acesso_reserva/<int:reserva_id>/', liberar_acesso_reserva, name='liberar_acesso_reserva'),





    path('mensagens/', mensagens_portaria, name='mensagens_portaria'),







    path('api/stats/', api_stats, name='api_stats'),

    path('api/moradores-offline/', api_moradores_offline, name='api_moradores_offline'),

    path('api/sync-offline/', api_sync_offline, name='api_sync_offline'),

    path('exportar_relatorio/', exportar_relatorio, name='exportar_relatorio'),





    path('morador/', portal_home, name='morador_home'),

    path('morador/completar-cadastro/', completar_cadastro, name='completar_cadastro'),

    path('morador/encomendas/', minhas_encomendas, name='morador_encomendas'),

    path('morador/solicitacoes/', minhas_solicitacoes, name='morador_solicitacoes'),

    path('morador/solicitacoes/nova/', nova_solicitacao, name='morador_nova_solicitacao'),

    path('morador/solicitacoes/<int:id>/', ver_solicitacao, name='morador_ver_solicitacao'),

    path('morador/avisos/', avisos, name='morador_avisos'),

    path('morador/mensagens/', mensagens, name='morador_mensagens'),

    path('morador/reservas/', minhas_reservas, name='morador_reservas'),

    path('morador/reservas/areas/', areas_disponiveis, name='morador_areas_disponiveis'),

    path('morador/reservas/nova/<int:area_id>/', fazer_reserva, name='morador_fazer_reserva'),

    path('morador/reservas/<int:reserva_id>/cancelar/', cancelar_reserva, name='morador_cancelar_reserva'),

    path('morador/ocorrencias/', ocorrencias, name='morador_ocorrencias'),

    path('morador/financeiro/', minhas_cobrancas, name='morador_cobrancas'),

    path('morador/perfil/editar/', editar_perfil_morador, name='editar_perfil_morador'),

    path('morador/documentos/', documentos_morador, name='morador_documentos'),

    path('morador/feedback/', feedback_morador, name='morador_feedback'),

    path('api/push/subscribe/', salvar_inscricao_push, name='salvar_inscricao_push'),

    path('api/push/unsubscribe/', remover_subscricao, name='remover_subscricao'),

    path('atualizar_preferencia_push/', atualizar_preferencia_push, name='atualizar_preferencia_push'),





    path('sindico/', portal_sindico_home, name='sindico_home'),

    path('sindico/selecionar/<int:condominio_id>/', selecionar_condominio, name='sindico_selecionar'),

    path('sindico/novo-condominio/', criar_condominio, name='sindico_criar_condominio'),

    path('sindico/painel/', painel_sindico, name='sindico_painel'),

    path('sindico/tarefas/', central_tarefas_sindico, name='sindico_tarefas'),

    path('sindico/moradores/', moradores_sindico, name='sindico_moradores'),

    path('sindico/moradores/<int:id>/editar/', sindico_morador_editar, name='sindico_morador_editar'),

    path('sindico/moradores/<int:id>/excluir/', sindico_morador_excluir, name='sindico_morador_excluir'),

    path('sindico/moradores/<int:morador_id>/resetar-senha/', resetar_senha_morador, name='sindico_resetar_senha'),

    path('sindico/solicitacoes/', solicitacoes_sindico, name='sindico_solicitacoes'),

    path('sindico/solicitacoes/responder/<int:solicitacao_id>/', responder_solicitacao_sindico, name='sindico_responder_solicitacao'),

    path('sindico/avisos/', avisos_sindico, name='sindico_avisos'),

    path('sindico/avisos/novo/', criar_aviso_sindico, name='sindico_criar_aviso'),

    path('sindico/avisos/<int:aviso_id>/editar/', editar_aviso_sindico, name='sindico_editar_aviso'),

    path('sindico/avisos/<int:aviso_id>/excluir/', excluir_aviso_sindico, name='sindico_excluir_aviso'),



    path('sindico/areas-comuns/', areas_comuns_sindico, name='sindico_areas_comuns'),

    path('sindico/areas-comuns/<int:area_id>/excluir/', excluir_area_sindico, name='sindico_excluir_area'),

    path('sindico/reservas/', reservas_sindico, name='sindico_reservas'),

    path('sindico/reservas/aprovar/<int:reserva_id>/', aprovar_reserva_sindico, name='sindico_aprovar_reserva'),

    path('sindico/reservas/recusar/<int:reserva_id>/', recusar_reserva_sindico, name='sindico_recusar_reserva'),

    path('sindico/financeiro/', financeiro_sindico, name='sindico_financeiro'),

    path('sindico/api/buscar-moradores/', buscar_moradores_ajax, name='buscar_moradores_ajax'),

    path('sindico/mensagens/', mensagens_sindico, name='sindico_mensagens'),

    path('sindico/ocorrencias/', ocorrencias_sindico, name='sindico_ocorrencias'),

    path('sindico/ocorrencias/<int:ocorrencia_id>/status/', alterar_status_ocorrencia, name='sindico_alterar_status_ocorrencia'),

    path('sindico/ocorrencias/<int:ocorrencia_id>/advertencia-pdf/', gerar_advertencia_pdf, name='sindico_gerar_advertencia_pdf'),

    path('sindico/notificacoes/', sindico_notificacoes, name='sindico_notificacoes'),

    path('sindico/notificacoes/<int:notificacao_id>/', redirecionar_notificacao, name='redirecionar_notificacao'),

    path('sindico/perfil/editar/', editar_perfil_sindico, name='editar_perfil_sindico'),

    path('sindico/documentos/', documentos_sindico, name='sindico_documentos'),

    path('sindico/portaria/', gerenciar_portaria, name='sindico_portaria'),

    path('sindico/feedbacks/', feedbacks_sindico, name='sindico_feedbacks'),



    path('sindico/condominio/<int:condominio_id>/', dashboard_condominio, name='sindico_dashboard'),

    path('zelador/', include('portaria.urls_zelador')),

]



















from django.urls import re_path

from django.views.static import serve as static_serve



urlpatterns += [

    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),

    re_path(r'^img/(?P<path>.*)$', static_serve, {'document_root': settings.BASE_DIR / 'img'}),

]
