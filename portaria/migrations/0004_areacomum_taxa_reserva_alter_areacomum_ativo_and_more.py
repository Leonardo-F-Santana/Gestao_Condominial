



from django.db import migrations, models





class Migration(migrations.Migration):



    dependencies = [

        ('portaria', '0003_mensagem'),

    ]



    operations = [

        migrations.AddField(

            model_name='areacomum',

            name='taxa_reserva',

            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Valor cobrado automaticamente ao aprovar a reserva (0 = Grátis)', max_digits=10, verbose_name='Taxa de Reserva (R$)'),

        ),

        migrations.AlterField(

            model_name='areacomum',

            name='ativo',

            field=models.BooleanField(default=True),

        ),

        migrations.AlterField(

            model_name='areacomum',

            name='capacidade',

            field=models.PositiveIntegerField(help_text='Capacidade máxima de pessoas', verbose_name='Capacidade'),

        ),

        migrations.AlterField(

            model_name='areacomum',

            name='horario_abertura',

            field=models.TimeField(verbose_name='Horário de Abertura'),

        ),

        migrations.AlterField(

            model_name='areacomum',

            name='horario_fechamento',

            field=models.TimeField(verbose_name='Horário de Fechamento'),

        ),

    ]

