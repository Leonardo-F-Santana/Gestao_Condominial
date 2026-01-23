from django.db import models

class Morador(models.Model):
    nome = models.CharField(max_length=190, verbose_name="Nome do Morador")
    cpf = models.CharField(max_length=14, verbose_name="CPF", blank=True, null=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone de Contato")
    
    # Detalhes da unidade
    bloco = models.CharField(max_length=10, verbose_name="Bloco", blank=True, null=True)
    apartamento = models.CharField(max_length=10, verbose_name="Número do Apartamento")

    def __str__(self):
        # Isso faz aparecer "Bloco A - 102 - João" nas listas
        if self.bloco:
            return f"{self.bloco} - {self.apartamento} - {self.nome}"
        return f"{self.apartamento} - {self.nome}"

class Visitante(models.Model):
    nome_completo = models.CharField(max_length=190, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=15, verbose_name="CPF")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    numero_casa = models.CharField(max_length=30, verbose_name="Número da Casa/Apto")
    placa_veiculo = models.CharField(max_length=7, blank=True, null=True, verbose_name="Placa do Carro")
    horario_chegada = models.DateTimeField(auto_now_add=True, verbose_name="Chegada")
    horario_saida = models.DateTimeField(null=True, blank=True, verbose_name="Saída")
    
    def __str__(self):
        return self.nome_completo
    
    def __str__(self):
        return self.nome_completo