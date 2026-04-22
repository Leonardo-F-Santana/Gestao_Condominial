



from django.db import migrations, models





class Migration(migrations.Migration):



    dependencies = [

        ('portaria', '0010_ocorrencia_foto_ocorrencia_resposta_sindico'),

    ]



    operations = [

        migrations.AddField(

            model_name='ocorrencia',

            name='advertencia_emitida',

            field=models.BooleanField(default=False, verbose_name='Advertência Emitida'),

        ),

    ]

