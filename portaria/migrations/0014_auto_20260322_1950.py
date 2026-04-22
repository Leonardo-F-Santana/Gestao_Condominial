



from django.db import migrations





def forward_func(apps, schema_editor):

    CustomUser = apps.get_model("portaria", "CustomUser")

    for user in CustomUser.objects.all():

        if user.condominio_id:

            user.condominios.add(user.condominio_id)



def reverse_func(apps, schema_editor):

    pass





class Migration(migrations.Migration):



    dependencies = [

        ('portaria', '0013_customuser_condominios'),

    ]



    operations = [

        migrations.RunPython(forward_func, reverse_func),

    ]

