

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0009_alter_notificacao_tipo_alter_solicitacao_tipo'),

    ]

    operations = [

        migrations.AddField(

            model_name='ocorrencia',

            name='foto',

            field=models.FileField(blank=True, null=True, upload_to='ocorrencias/%Y/%m/', verbose_name='Foto/Prova'),

        ),

        migrations.AddField(

            model_name='ocorrencia',

            name='resposta_sindico',

            field=models.TextField(blank=True, verbose_name='Resposta do Síndico'),

        ),

    ]

