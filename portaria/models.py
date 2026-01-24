from django.db import models

class Morador(models.Model):
    nome = models.CharField(max_length=190, verbose_name="Nome do Morador")
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True, null=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone de Contato")
    
    bloco = models.CharField(max_length=10, verbose_name="Bloco", blank=True, null=True)
    apartamento = models.CharField(max_length=10, verbose_name="Número do Apartamento")

    class Meta:
        verbose_name_plural = "Moradores"

    def __str__(self):
        if self.bloco:
            return f"{self.bloco} - {self.apartamento} - {self.nome}"
        return f"{self.apartamento} - {self.nome}"

class Visitante(models.Model):
    nome_completo = models.CharField(max_length=190, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", blank=True, null=True)
    numero_casa = models.CharField(max_length=30, verbose_name="Número da Casa/Apto (Antigo)", blank=True)
    
    morador_responsavel = models.ForeignKey(
        Morador, 
        on_delete=models.PROTECT, 
        verbose_name="Morador Responsável",
        blank=True, 
        null=True
    )
    
    placa_veiculo = models.CharField(max_length=7, blank=True, null=True, verbose_name="Placa do Carro")
    quem_autorizou = models.CharField(max_length=100, verbose_name="Quem Autorizou", blank=True)
    observacoes = models.TextField(verbose_name="Observações", blank=True)
    
    horario_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Chegada")
    horario_saida = models.DateTimeField(null=True, blank=True, verbose_name="Saída")
    
    class Meta:
        verbose_name_plural = "Visitantes"
    
    def __str__(self):
        return self.nome_completo


class Encomenda(models.Model):
    morador = models.ForeignKey(Morador, on_delete=models.CASCADE, verbose_name="Para o Morador")
    data_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Data de Chegada")
    volume = models.CharField(max_length=100, verbose_name="Volume", help_text="Ex: Caixa Amazon, Envelope, Ifood...")
    entregue = models.BooleanField(default=False, verbose_name="Já foi entregue?")
    data_entrega = models.DateTimeField(null=True, blank=True, verbose_name="Data da Entrega")
    quem_retirou = models.CharField(max_length=100, blank=True, verbose_name="Quem retirou?")
    notificado = models.BooleanField(default=False, verbose_name="Morador foi avisado?")
    documento_retirada = models.CharField(max_length=50, blank=True, verbose_name="Documento de quem retirou")

    def __str__(self):
        return f"{self.volume} - {self.morador}"

    class Meta:
        verbose_name_plural = "Encomendas"