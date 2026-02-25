"""
Data migration: preenche o campo condominio em Visitante, Encomenda e Solicitacao
a partir do morador vinculado (quando disponível).
"""
from django.db import migrations


def preencher_condominio(apps, schema_editor):
    Visitante = apps.get_model('portaria', 'Visitante')
    Encomenda = apps.get_model('portaria', 'Encomenda')
    Solicitacao = apps.get_model('portaria', 'Solicitacao')

    # Visitantes: preencher a partir do morador_responsavel
    for v in Visitante.objects.filter(condominio__isnull=True, morador_responsavel__isnull=False):
        if v.morador_responsavel and v.morador_responsavel.condominio:
            v.condominio = v.morador_responsavel.condominio
            v.save(update_fields=['condominio'])

    # Encomendas: preencher a partir do morador
    for e in Encomenda.objects.filter(condominio__isnull=True, morador__isnull=False):
        if e.morador and e.morador.condominio:
            e.condominio = e.morador.condominio
            e.save(update_fields=['condominio'])

    # Solicitações: preencher a partir do morador
    for s in Solicitacao.objects.filter(condominio__isnull=True, morador__isnull=False):
        if s.morador and s.morador.condominio:
            s.condominio = s.morador.condominio
            s.save(update_fields=['condominio'])


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0024_add_porteiro_and_condominio_fks'),
    ]

    operations = [
        migrations.RunPython(preencher_condominio, migrations.RunPython.noop),
    ]
