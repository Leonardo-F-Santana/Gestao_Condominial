from django.urls import path
from .views_zelador import (
    zelador_home, checklists_zelador, concluir_checklist,
    ordens_servico_zelador, mudar_status_os, agenda_zelador,
    livro_ocorrencias_zelador, avisos_zelador, prestadores_zelador,
    estoque_zelador, atualizar_estoque, zelador_notificacoes
)

urlpatterns = [
    path('', zelador_home, name='zelador_home'),
    path('notificacoes/', zelador_notificacoes, name='zelador_notificacoes'),
    path('checklists/', checklists_zelador, name='zelador_checklists'),
    path('checklists/<int:pk>/concluir/', concluir_checklist, name='zelador_concluir_checklist'),
    path('os/', ordens_servico_zelador, name='zelador_os'),
    path('os/<int:pk>/status/', mudar_status_os, name='zelador_mudar_status_os'),
    path('agenda/', agenda_zelador, name='zelador_agenda'),
    path('ocorrencias/', livro_ocorrencias_zelador, name='zelador_ocorrencias'),
    path('avisos/', avisos_zelador, name='zelador_avisos'),
    path('prestadores/', prestadores_zelador, name='zelador_prestadores'),
    path('estoque/', estoque_zelador, name='zelador_estoque'),
    path('estoque/<int:pk>/atualizar/', atualizar_estoque, name='zelador_atualizar_estoque'),
]
