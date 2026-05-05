

import django.db.models.deletion

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0001_initial'),

    ]

    operations = [

        migrations.CreateModel(

            name='Cobranca',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('descricao', models.CharField(default='Taxa Condominial', max_length=200, verbose_name='Descrição da Cobrança')),

                ('valor', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor (R$)')),

                ('data_vencimento', models.DateField(verbose_name='Data de Vencimento')),

                ('data_pagamento', models.DateField(blank=True, null=True, verbose_name='Data do Pagamento')),

                ('status', models.CharField(choices=[('PENDENTE', '🟡 Pendente'), ('PAGO', '🟢 Pago'), ('ATRASADO', '🔴 Atrasado'), ('CANCELADO', '⚫ Cancelado')], default='PENDENTE', max_length=20, verbose_name='Status')),

                ('data_criacao', models.DateTimeField(auto_now_add=True, verbose_name='Gerado em')),

                ('condominio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cobrancas', to='portaria.condominio', verbose_name='Condomínio')),

                ('morador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cobrancas', to='portaria.morador', verbose_name='Morador')),

            ],

            options={

                'verbose_name': 'Cobrança',

                'verbose_name_plural': 'Cobranças',

                'ordering': ['-data_vencimento'],

            },

        ),

    ]

