

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0016_notificacao_condominio'),

    ]

    operations = [

        migrations.AddField(

            model_name='morador',

            name='status_aprovacao',

            field=models.CharField(choices=[('AGUARDANDO', 'Aguardando Aprovação'), ('APROVADO', 'Aprovado'), ('RECUSADO', 'Recusado/Inativo')], default='APROVADO', max_length=20, verbose_name='Status de Aprovação'),

        ),

    ]

