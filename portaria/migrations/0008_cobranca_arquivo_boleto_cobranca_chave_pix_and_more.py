

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0007_mensagem_resposta_a'),

    ]

    operations = [

        migrations.AddField(

            model_name='cobranca',

            name='arquivo_boleto',

            field=models.FileField(blank=True, null=True, upload_to='cobrancas/boletos/', verbose_name='Arquivo do Boleto'),

        ),

        migrations.AddField(

            model_name='cobranca',

            name='chave_pix',

            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Chave PIX ou Link'),

        ),

        migrations.AddField(

            model_name='cobranca',

            name='comprovante',

            field=models.FileField(blank=True, null=True, upload_to='cobrancas/comprovantes/', verbose_name='Comprovante de Pagamento'),

        ),

        migrations.AlterField(

            model_name='cobranca',

            name='status',

            field=models.CharField(choices=[('PENDENTE', '🟡 Pendente'), ('EM_ANALISE', '🟠 Em Análise'), ('PAGO', '🟢 Pago'), ('ATRASADO', '🔴 Atrasado'), ('CANCELADO', '⚫ Cancelado')], default='PENDENTE', max_length=20, verbose_name='Status'),

        ),

    ]

