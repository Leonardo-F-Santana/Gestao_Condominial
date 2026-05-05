

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0012_documentocondominio'),

    ]

    operations = [

        migrations.AddField(

            model_name='customuser',

            name='condominios',

            field=models.ManyToManyField(blank=True, related_name='usuarios', to='portaria.condominio'),

        ),

    ]

