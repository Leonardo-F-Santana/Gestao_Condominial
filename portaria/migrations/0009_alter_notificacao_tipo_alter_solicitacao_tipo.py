

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [

        ('portaria', '0008_cobranca_arquivo_boleto_cobranca_chave_pix_and_more'),

    ]

    operations = [

        migrations.AlterField(

            model_name='notificacao',

            name='tipo',

            field=models.CharField(choices=[('aviso', '📢 Novo Aviso'), ('solicitacao', '📋 Nova Solicitação'), ('resposta_solicitacao', '💬 Resposta de Solicitação'), ('reserva', '📅 Reserva de Espaço'), ('ocorrencia', '🚨 Nova Ocorrência')], max_length=30),

        ),

        migrations.AlterField(

            model_name='solicitacao',

            name='tipo',

            field=models.CharField(choices=[('DUVIDA', '❓ Dúvida'), ('SUGESTAO', '💡 Sugestão'), ('MANUTENCAO', '🛠️ Manutenção'), ('MUDANCA', '🚚 Mudança'), ('OUTRO', '📝 Outro')], max_length=20, verbose_name='Tipo de Solicitação'),

        ),

    ]

