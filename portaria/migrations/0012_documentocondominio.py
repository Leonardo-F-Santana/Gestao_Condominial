

import django.db.models.deletion

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0011_ocorrencia_advertencia_emitida'),

    ]

    operations = [

        migrations.CreateModel(

            name='DocumentoCondominio',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('titulo', models.CharField(max_length=200, verbose_name='Título do Documento')),

                ('categoria', models.CharField(choices=[('CONVENCAO', 'Convenção'), ('REGIMENTO', 'Regimento Interno'), ('ATA', 'Ata de Assembleia'), ('FINANCEIRO', 'Relatório Financeiro'), ('OUTROS', 'Outros')], default='OUTROS', max_length=20, verbose_name='Categoria')),

                ('arquivo', models.FileField(upload_to='documentos/%Y/%m/', verbose_name='Arquivo')),

                ('data_upload', models.DateTimeField(auto_now_add=True, verbose_name='Data de Upload')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='portaria.condominio')),

            ],

            options={

                'verbose_name': 'Documento',

                'verbose_name_plural': 'Documentos',

                'ordering': ['-data_upload'],

            },

        ),

    ]

