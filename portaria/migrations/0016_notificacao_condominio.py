

import django.db.models.deletion

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0015_remove_customuser_condominio'),

    ]

    operations = [

        migrations.AddField(

            model_name='notificacao',

            name='condominio',

            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to='portaria.condominio'),

        ),

    ]

