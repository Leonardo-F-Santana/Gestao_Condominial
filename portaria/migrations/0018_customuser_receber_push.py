

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0017_morador_status_aprovacao'),

    ]

    operations = [

        migrations.AddField(

            model_name='customuser',

            name='receber_push',

            field=models.BooleanField(default=False, verbose_name='Deseja receber notificações push?'),

        ),

    ]

