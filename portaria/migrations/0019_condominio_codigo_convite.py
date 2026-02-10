import uuid
from django.db import migrations, models


def gerar_uuids_unicos(apps, schema_editor):
    """Gera UUIDs únicos para condominios existentes"""
    Condominio = apps.get_model('portaria', 'Condominio')
    for cond in Condominio.objects.all():
        cond.codigo_convite = uuid.uuid4()
        cond.save(update_fields=['codigo_convite'])


class Migration(migrations.Migration):

    dependencies = [
        ('portaria', '0018_aviso_condominio_aviso_data_expiracao_aviso_imagem'),
    ]

    operations = [
        # Passo 1: Adicionar campo sem unique
        migrations.AddField(
            model_name='condominio',
            name='codigo_convite',
            field=models.UUIDField(default=uuid.uuid4, null=True, verbose_name='Código de Convite'),
        ),
        # Passo 2: Popular registros existentes
        migrations.RunPython(gerar_uuids_unicos, migrations.RunPython.noop),
        # Passo 3: Tornar unique e não-nulo
        migrations.AlterField(
            model_name='condominio',
            name='codigo_convite',
            field=models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='Código de Convite'),
        ),
    ]
