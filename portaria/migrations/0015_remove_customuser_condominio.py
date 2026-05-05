

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0014_auto_20260322_1950'),

    ]

    operations = [

        migrations.RemoveField(

            model_name='customuser',

            name='condominio',

        ),

    ]

